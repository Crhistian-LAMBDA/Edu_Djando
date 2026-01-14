from django.db import models
from django.utils import timezone


class RecordatorioVencimiento(models.Model):
    class TipoRecordatorio(models.TextChoices):
        D3_ESTUDIANTE = 'D3_ESTUDIANTE', '3 días antes (estudiante)'
        D1_ESTUDIANTE = 'D1_ESTUDIANTE', '1 día antes (estudiante)'
        D1_DOCENTE = 'D1_DOCENTE', '1 día antes (docente)'

    tarea = models.ForeignKey(
        'evaluaciones.Tarea',
        on_delete=models.CASCADE,
        related_name='recordatorios_vencimiento',
    )

    tipo_recordatorio = models.CharField(max_length=20, choices=TipoRecordatorio.choices)
    scheduled_for = models.DateTimeField(help_text='Fecha/hora programada para enviar el recordatorio')
    sent_at = models.DateTimeField(null=True, blank=True, help_text='Fecha/hora real de envío')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tarea', 'tipo_recordatorio'],
                name='uniq_recordatorio_por_tarea_y_tipo',
            )
        ]
        indexes = [
            models.Index(fields=['sent_at', 'scheduled_for']),
        ]

    def marcar_enviado(self):
        if not self.sent_at:
            self.sent_at = timezone.now()
            self.save(update_fields=['sent_at'])
