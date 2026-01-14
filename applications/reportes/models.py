from django.db import models


class ReporteMensual(models.Model):
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()

    fecha_generacion = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['year', 'month'], name='uniq_reporte_mensual_year_month'),
        ]
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Reporte mensual {self.year}-{self.month:02d}"
