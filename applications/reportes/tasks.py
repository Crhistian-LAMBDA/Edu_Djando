from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models, transaction
from django.utils import timezone

from celery import shared_task

from applications.usuarios.models import Usuario
from applications.usuarios.models import Rol

from .models import ReporteMensual
from .services.mensual import generar_reporte_mensual_data
from .services.render import render_excel_bytes, render_html_resumen, render_pdf_bytes


PERMISO_DESTINATARIOS = 'recibir_notificacion_estado_mensual'


def _get_recipients_emails() -> list[str]:
    # Usuarios que tienen el permiso asignado vía roles (M2M) o por `rol` legacy.
    legacy_role_tipos = list(
        Rol.objects.filter(permisos_asignados__codigo=PERMISO_DESTINATARIOS)
        .values_list('tipo', flat=True)
        .distinct()
    )

    qs = (
        Usuario.objects
        .filter(is_active=True)
        .filter(
            models.Q(roles__permisos_asignados__codigo=PERMISO_DESTINATARIOS)
            | models.Q(rol__in=legacy_role_tipos)
        )
        .distinct()
    )

    emails = sorted({(getattr(u, 'email', '') or '').strip() for u in qs})
    return [e for e in emails if e]


def _target_month_for_auto(now=None) -> tuple[int, int]:
    now = now or timezone.localdate()
    # Auto: el 1 de cada mes genera el mes anterior
    year = now.year
    month = now.month

    if month == 1:
        return year - 1, 12
    return year, month - 1


@shared_task
def generar_y_enviar_reporte_mensual(year: int | None = None, month: int | None = None, force_resend: bool = False):
    if year is None or month is None:
        year, month = _target_month_for_auto()

    with transaction.atomic():
        reporte, created = ReporteMensual.objects.get_or_create(
            year=year,
            month=month,
            defaults={'data': {}},
        )

        # Evitar duplicados: si ya se envió y no se fuerza, no repetir.
        if reporte.sent_at and not force_resend:
            return f"Reporte {year}-{month:02d} ya enviado"

        data = generar_reporte_mensual_data(year=year, month=month)
        reporte.data = data
        reporte.save(update_fields=['data'])

    recipients = _get_recipients_emails()
    if not recipients:
        return f"Reporte {year}-{month:02d} generado pero sin destinatarios con permiso"

    html = render_html_resumen(data)
    xlsx_bytes = render_excel_bytes(data)
    pdf_bytes = render_pdf_bytes(data)

    subject = f"Consolidado mensual académico {year}-{month:02d}"

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

    email = EmailMessage(
        subject=subject,
        body=html,
        from_email=from_email,
        to=[from_email] if from_email else [],
        bcc=recipients,
    )
    email.content_subtype = 'html'

    email.attach(
        filename=f"consolidado_{year}-{month:02d}.xlsx",
        content=xlsx_bytes,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    email.attach(
        filename=f"consolidado_{year}-{month:02d}.pdf",
        content=pdf_bytes,
        mimetype='application/pdf',
    )

    email.send(fail_silently=False)

    ReporteMensual.objects.filter(id=reporte.id).update(sent_at=timezone.now())

    return f"Reporte {year}-{month:02d} enviado a {len(recipients)} usuarios"
