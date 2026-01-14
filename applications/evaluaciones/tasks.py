"""
Tareas Celery para notificaciones de evaluaciones
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from applications.evaluaciones.models import Tarea, EntregaTarea


@shared_task
def enviar_notificacion_tarea(tarea_id):
    """
    Envía notificación por email a todos los estudiantes inscritos
    cuando se publica una nueva tarea
    """
    try:
        tarea = Tarea.objects.select_related('asignatura').get(id=tarea_id)
    except Tarea.DoesNotExist:
        return f"Tarea {tarea_id} no encontrada"
    
    # Estudiantes inscritos = estudiantes con matrícula activa en la asignatura
    # (consistente con el resto del sistema: solo matrículas con horario asignado)
    from applications.matriculas.models import Matricula

    matriculas = (
        Matricula.objects
        .select_related('estudiante')
        .filter(asignatura=tarea.asignatura, estado='activa', horario__isnull=False)
        .exclude(horario='')
        .distinct()
    )

    estudiantes = [m.estudiante for m in matriculas]
    
    if not estudiantes:
        return f"No hay estudiantes inscritos en {tarea.asignatura.codigo}"
    
    # Preparar datos del email
    asunto = f"Nueva tarea publicada: {tarea.titulo}"
    
    contexto = {
        'tarea': tarea,
        'asignatura': tarea.asignatura,
        'tipo_display': tarea.get_tipo_tarea_display(),
    }
    
    # Lista de destinatarios
    destinatarios = sorted({est.email for est in estudiantes if getattr(est, 'email', None)})
    
    if not destinatarios:
        return "No hay emails válidos para enviar"
    
    # Enviar email
    try:
        send_mail(
            subject=asunto,
            message=(
                f"Se ha publicado una nueva evaluación ({tarea.get_tipo_tarea_display()}):\n\n"
                f"Título: {tarea.titulo}\n"
                f"Asignatura: {tarea.asignatura.nombre} ({tarea.asignatura.codigo})\n"
                f"Fecha de publicación: {tarea.fecha_publicacion}\n"
                f"Fecha de vencimiento: {tarea.fecha_vencimiento}\n\n"
                f"Descripción:\n{tarea.descripcion or 'Sin descripción'}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatarios,
            fail_silently=False,
        )
        return f"Notificación enviada a {len(destinatarios)} estudiantes"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"


@shared_task
def enviar_recordatorio_vencimiento(tarea_id):
    """
    Envía recordatorio 24 horas antes del vencimiento
    (Para implementar con Celery Beat)
    """
    try:
        tarea = Tarea.objects.select_related('asignatura').get(id=tarea_id)
    except Tarea.DoesNotExist:
        return f"Tarea {tarea_id} no encontrada"
    
    # TODO: Implementar cuando exista modelo de Inscripción
    return f"Recordatorio de vencimiento para: {tarea.titulo}"


@shared_task
def notificar_docente_nueva_entrega(entrega_id):
    """
    Notifica al docente cuando un estudiante sube una entrega
    """
    try:
        entrega = EntregaTarea.objects.select_related(
            'tarea', 'tarea__asignatura', 'estudiante'
        ).get(id=entrega_id)
    except EntregaTarea.DoesNotExist:
        return f"Entrega {entrega_id} no encontrada"
    
    # Obtener un docente asignado a la asignatura (modelo actual: ProfesorAsignatura)
    docente = (
        entrega.tarea.asignatura.profesores_asignados
        .select_related('profesor')
        .values_list('profesor', flat=True)
        .first()
    )

    if not docente:
        return "No hay docente asignado"

    from applications.usuarios.models import Usuario
    docente_obj = Usuario.objects.filter(id=docente).first()

    if not docente_obj or not getattr(docente_obj, 'email', None):
        return "No hay email válido del docente"
    
    # Preparar datos del email
    asunto = f"Nueva entrega: {entrega.tarea.titulo} - {entrega.estudiante.get_full_name()}"
    
    contexto = {
        'entrega': entrega,
        'tarea': entrega.tarea,
        'estudiante': entrega.estudiante,
        'asignatura': entrega.tarea.asignatura,
    }
    
    # Renderizar template HTML (si existe)
    # mensaje_html = render_to_string('evaluaciones/email_nueva_entrega.html', contexto)
    
    # Mensaje de texto plano
    mensaje = f"""
Hola {(docente_obj.get_full_name() or docente_obj.username).strip()},

El estudiante {entrega.estudiante.get_full_name()} ({entrega.estudiante.username}) ha subido una nueva entrega:

Tarea: {entrega.tarea.titulo}
Asignatura: {entrega.tarea.asignatura.nombre} ({entrega.tarea.asignatura.codigo})
Fecha de entrega: {entrega.fecha_entrega.strftime('%d/%m/%Y %H:%M')}
Estado: {'Tardía' if entrega.fue_tardia else 'A tiempo'}

Comentarios del estudiante:
{entrega.comentarios_estudiante or 'Sin comentarios'}

Por favor, revisa y califica la entrega en el sistema.

Saludos,
Sistema de Gestión Académica
    """.strip()
    
    # Enviar email
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[docente_obj.email],
            fail_silently=False,
        )
        return f"Notificación enviada al docente {docente_obj.email}"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"


@shared_task
def notificar_estudiante_calificacion(entrega_id):
    """Notifica al estudiante cuando su entrega es calificada."""
    try:
        entrega = EntregaTarea.objects.select_related(
            'tarea', 'tarea__asignatura', 'estudiante'
        ).get(id=entrega_id)
    except EntregaTarea.DoesNotExist:
        return f"Entrega {entrega_id} no encontrada"

    estudiante = entrega.estudiante
    estudiante_email = (getattr(estudiante, 'email', '') or '').strip()
    if not estudiante_email:
        return "No hay email válido del estudiante"

    # Solo notificar si está efectivamente calificada
    if entrega.calificacion is None:
        return "Entrega sin calificación; no se notifica"

    asunto = f"Calificación publicada: {entrega.tarea.titulo}"

    nombre_est = (getattr(estudiante, 'get_full_name', lambda: '')() or getattr(estudiante, 'username', '')).strip()
    if not nombre_est:
        nombre_est = 'Estudiante'

    nota = float(entrega.calificacion)
    retro = (entrega.comentarios_docente or '').strip() or 'Sin retroalimentación'

    mensaje = f"""
Hola {nombre_est},

Tu entrega ha sido calificada.

Asignatura: {entrega.tarea.asignatura.nombre} ({entrega.tarea.asignatura.codigo})
Tarea: {entrega.tarea.titulo}
Nota: {nota}
Fecha de calificación: {entrega.fecha_calificacion.strftime('%d/%m/%Y %H:%M') if entrega.fecha_calificacion else ''}

Retroalimentación del docente:
{retro}

Saludos,
Sistema de Gestión Académica
    """.strip()

    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[estudiante_email],
            fail_silently=False,
        )
        return f"Notificación enviada al estudiante {estudiante_email}"
    except Exception as e:
        return f"Error al enviar email: {str(e)}"
