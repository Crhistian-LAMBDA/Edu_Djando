"""
Tareas Celery para notificaciones de evaluaciones
"""
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from applications.evaluaciones.models import Tarea


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
    
    # TODO: Cuando exista el modelo de Inscripción/Matrícula, obtener estudiantes
    # Por ahora, simular con un placeholder
    # estudiantes = tarea.asignatura.estudiantes_inscritos.filter(activo=True)
    
    # Placeholder: obtener estudiantes (cuando se implemente el modelo)
    estudiantes = []  # Aquí irían los estudiantes reales
    
    if not estudiantes:
        return f"No hay estudiantes inscritos en {tarea.asignatura.codigo}"
    
    # Preparar datos del email
    asunto = f"Nueva tarea publicada: {tarea.titulo}"
    
    contexto = {
        'tarea': tarea,
        'asignatura': tarea.asignatura,
        'tipo_display': tarea.get_tipo_tarea_display(),
    }
    
    # Renderizar template HTML
    mensaje_html = render_to_string('evaluaciones/email_nueva_tarea.html', contexto)
    
    # Lista de destinatarios
    destinatarios = [est.email for est in estudiantes if est.email]
    
    if not destinatarios:
        return "No hay emails válidos para enviar"
    
    # Enviar email
    try:
        send_mail(
            subject=asunto,
            message=f"Nueva tarea: {tarea.titulo}\n\nAsignatura: {tarea.asignatura.nombre}\nFecha de vencimiento: {tarea.fecha_vencimiento}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=destinatarios,
            html_message=mensaje_html,
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
