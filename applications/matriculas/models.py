# models.py para Matriculas
from django.db import models
from django.conf import settings
from applications.academico.models import Asignatura, PeriodoAcademico

from django.db.models import Q

class Matricula(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matriculas',
        limit_choices_to=Q(rol='estudiante') | Q(roles__tipo='estudiante')
    )
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='matriculas')
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, related_name='matriculas')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='activa')
    horario = models.CharField(max_length=100, blank=True, null=True, help_text='Horario de estudio: Ejemplo Lunes 8-10am o formato JSON')

    class Meta:
        verbose_name = 'Matrícula-Asignatura'
        verbose_name_plural = 'Matrículas-Asignaturas'
        unique_together = ('estudiante', 'asignatura', 'periodo')

    def __str__(self):
        return f"{self.estudiante} - {self.asignatura} ({self.periodo})"