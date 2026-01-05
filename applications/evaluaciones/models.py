"""
Modelos de evaluaciones - Tareas y Exámenes
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from applications.academico.models import Asignatura


class Tarea(models.Model):
    """
    Modelo para tareas y exámenes de una asignatura
    """
    TIPO_CHOICES = (
        ('tarea', 'Tarea'),
        ('examen', 'Examen'),
        ('quiz', 'Quiz'),
        ('proyecto', 'Proyecto'),
        ('participacion', 'Participación'),
    )
    
    ESTADO_CHOICES = (
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
    )
    
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='tareas',
        help_text='Asignatura a la que pertenece esta tarea'
    )
    titulo = models.CharField(
        max_length=200,
        help_text='Título de la tarea o examen'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción detallada de la tarea'
    )
    tipo_tarea = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='tarea',
        help_text='Tipo de evaluación'
    )
    peso_porcentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Peso en porcentaje (0-100). Ej: 15.50 para 15.5%'
    )
    fecha_publicacion = models.DateTimeField(
        help_text='Fecha y hora en que la tarea será visible para estudiantes'
    )
    fecha_vencimiento = models.DateTimeField(
        help_text='Fecha y hora límite para entregar la tarea'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        help_text='Estado actual de la tarea'
    )
    permite_entrega_tardia = models.BooleanField(
        default=False,
        help_text='Permite que estudiantes entreguen después del vencimiento'
    )
    archivo_adjunto = models.FileField(
        upload_to='tareas/adjuntos/%Y/%m/',
        blank=True,
        null=True,
        help_text='Archivo adjunto con instrucciones (PDF, DOCX, etc.)'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'
        ordering = ['-fecha_publicacion']
        constraints = [
            models.CheckConstraint(
                check=models.Q(peso_porcentual__gte=0) & models.Q(peso_porcentual__lte=100),
                name='peso_valido'
            )
        ]
    
    def __str__(self):
        return f"{self.asignatura.codigo} - {self.titulo}"
    
    def clean(self):
        """
        Validaciones a nivel de modelo
        """
        # Validar que fecha_vencimiento sea posterior a fecha_publicacion
        if self.fecha_vencimiento and self.fecha_publicacion:
            if self.fecha_vencimiento <= self.fecha_publicacion:
                raise ValidationError({
                    'fecha_vencimiento': 'La fecha de vencimiento debe ser posterior a la fecha de publicación.'
                })
        
        # Validar título único por asignatura
        if self.asignatura_id:
            existe = Tarea.objects.filter(
                asignatura=self.asignatura,
                titulo__iexact=self.titulo
            ).exclude(pk=self.pk).exists()
            
            if existe:
                raise ValidationError({
                    'titulo': f'Ya existe una tarea con el título "{self.titulo}" en esta asignatura.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def esta_vencida(self):
        """Retorna True si la fecha de vencimiento ya pasó"""
        return timezone.now() > self.fecha_vencimiento
    
    @property
    def esta_publicada(self):
        """Retorna True si la tarea está publicada y visible"""
        return self.estado == 'publicada' and timezone.now() >= self.fecha_publicacion
