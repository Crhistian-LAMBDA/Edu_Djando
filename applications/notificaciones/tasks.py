from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone

from celery import shared_task

from applications.matriculas.models import Matricula
from applications.usuarios.models import Usuario

from .models import RecordatorioVencimiento


def _get_docente_responsable(asignatura):
    """Obtiene el primer docente asignado a la asignatura (modelo actual)."""
    docente_id = (
        asignatura.profesores_asignados
        .values_list('profesor', flat=True)
        .first()
    )
    if not docente_id:
        return None

    docente = Usuario.objects.filter(id=docente_id).first()
    if not docente:
        return None

    email = (getattr(docente, 'email', '') or '').strip()
    if not email:
        return None

    nombre = (getattr(docente, 'get_full_name', lambda: '')() or getattr(docente, 'username', '')).strip()
    return {
        'id': docente.id,
        'email': email,
        'nombre': nombre or email,
    }


def _get_estudiantes_emails(asignatura):
    matriculas = (
        Matricula.objects
        .select_related('estudiante')
        .filter(asignatura=asignatura, estado='activa', horario__isnull=False)
        .exclude(horario='')
        .distinct()
    )
    emails = sorted({(getattr(m.estudiante, 'email', '') or '').strip() for m in matriculas if getattr(m.estudiante, 'email', None)})
    return [e for e in emails if e]


def _render_message(recordatorio: RecordatorioVencimiento):
    tarea = recordatorio.tarea
    asignatura = tarea.asignatura

    docente = _get_docente_responsable(asignatura)
    docente_nombre = (docente['nombre'] if docente else 'No asignado')

    fecha_envio = timezone.now()
    tipo = recordatorio.get_tipo_recordatorio_display()

    # Campos requeridos por CA: asignatura, titulo_tarea, fecha_vencimiento,
    # docente_responsable, tipo_recordatorio, fecha_envio.
    asunto = f"Recordatorio ({tipo}): {tarea.titulo}"
    cuerpo = (
        f"Asignatura: {asignatura.nombre} ({asignatura.codigo})\n"
        f"Título tarea: {tarea.titulo}\n"
        f"Fecha vencimiento: {tarea.fecha_vencimiento}\n"
        f"Docente responsable: {docente_nombre}\n"
        f"Tipo recordatorio: {tipo}\n"
        f"Fecha envío: {fecha_envio}\n"
    )

    return asunto, cuerpo


@shared_task
def dispatch_recordatorios_vencimiento(batch_size: int = 200):
    """Despacha recordatorios pendientes y marca enviados (evita duplicados)."""
    now = timezone.now()

    with transaction.atomic():
        pendientes = (
            RecordatorioVencimiento.objects
            .select_for_update(skip_locked=True)
            .select_related('tarea', 'tarea__asignatura')
            .filter(sent_at__isnull=True, scheduled_for__lte=now)
            .order_by('scheduled_for')[:batch_size]
        )

        # Materializamos dentro del lock
        pendientes = list(pendientes)

    enviados = 0
    for recordatorio in pendientes:
        result = enviar_recordatorio_vencimiento.delay(recordatorio.id)
        # No esperamos el resultado; el envío se hace en otra task
        enviados += 1

    return f"Encolados {enviados} recordatorios"


@shared_task
def enviar_recordatorio_vencimiento(recordatorio_id: int):
    try:
        recordatorio = (
            RecordatorioVencimiento.objects
            .select_related('tarea', 'tarea__asignatura')
            .get(id=recordatorio_id)
        )
    except RecordatorioVencimiento.DoesNotExist:
        return f"Recordatorio {recordatorio_id} no existe"

    # Idempotencia: si ya se envió, no repetir.
    if recordatorio.sent_at:
        return f"Recordatorio {recordatorio_id} ya enviado"

    tarea = recordatorio.tarea
    asignatura = tarea.asignatura

    asunto, cuerpo = _render_message(recordatorio)

    destinatarios = []
    if recordatorio.tipo_recordatorio in (
        RecordatorioVencimiento.TipoRecordatorio.D3_ESTUDIANTE,
        RecordatorioVencimiento.TipoRecordatorio.D1_ESTUDIANTE,
    ):
        destinatarios = _get_estudiantes_emails(asignatura)

    elif recordatorio.tipo_recordatorio == RecordatorioVencimiento.TipoRecordatorio.D1_DOCENTE:
        docente = _get_docente_responsable(asignatura)
        destinatarios = [docente['email']] if docente else []

    if not destinatarios:
        # Marcamos como "enviado" para evitar loops infinitos por falta de emails.
        recordatorio.marcar_enviado()
        return f"Sin destinatarios; recordatorio {recordatorio_id} marcado como enviado"

    try:
        # Enviamos a todos en BCC para no exponer correos de estudiantes.
        email = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            to=[getattr(settings, 'DEFAULT_FROM_EMAIL', None)] if recordatorio.tipo_recordatorio != RecordatorioVencimiento.TipoRecordatorio.D1_DOCENTE else destinatarios,
            bcc=destinatarios if recordatorio.tipo_recordatorio != RecordatorioVencimiento.TipoRecordatorio.D1_DOCENTE else None,
        )
        email.send(fail_silently=False)
        recordatorio.marcar_enviado()
        return f"Recordatorio {recordatorio_id} enviado a {len(destinatarios)} destinatarios"
    except Exception as e:
        return f"Error enviando recordatorio {recordatorio_id}: {str(e)}"
