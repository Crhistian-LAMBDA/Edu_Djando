from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from applications.evaluaciones.models import Tarea

from .models import RecordatorioVencimiento


def _build_schedule(fecha_vencimiento):
    # Si no hay fecha, no se programa nada.
    if not fecha_vencimiento:
        return None

    # Usamos la hora exacta del vencimiento para los offsets.
    # Regla: 3 días antes y 1 día antes.
    return {
        RecordatorioVencimiento.TipoRecordatorio.D3_ESTUDIANTE: fecha_vencimiento - timedelta(days=3),
        RecordatorioVencimiento.TipoRecordatorio.D1_ESTUDIANTE: fecha_vencimiento - timedelta(days=1),
        RecordatorioVencimiento.TipoRecordatorio.D1_DOCENTE: fecha_vencimiento - timedelta(days=1),
    }


@receiver(post_save, sender=Tarea)
def programar_o_reprogramar_recordatorios(sender, instance: Tarea, created, **kwargs):
    fecha_venc = instance.fecha_vencimiento
    schedule = _build_schedule(fecha_venc)
    if not schedule:
        return

    # Crear o actualizar recordatorios pendientes.
    for tipo, scheduled_for in schedule.items():
        # Si ya fue enviado, no lo tocamos (evita duplicados retroactivos).
        obj, _ = RecordatorioVencimiento.objects.get_or_create(
            tarea=instance,
            tipo_recordatorio=tipo,
            defaults={'scheduled_for': scheduled_for},
        )

        if obj.sent_at:
            continue

        # Reprogramación: si cambió fecha_vencimiento, actualizamos scheduled_for.
        if obj.scheduled_for != scheduled_for:
            obj.scheduled_for = scheduled_for
            obj.save(update_fields=['scheduled_for', 'updated_at'])
