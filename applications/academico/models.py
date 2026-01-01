"""
Modelos académicos
"""
from django.db import models
from django.conf import settings


class Facultad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Facultad'
        verbose_name_plural = 'Facultades'
    
    def __str__(self):
        return self.nombre


class Asignatura(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    creditos = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Programa(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.CASCADE,
        related_name='programas'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Programa'
        verbose_name_plural = 'Programas'
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ProfesorAsignatura(models.Model):
    """Tabla intermedia para relación N-to-N entre Profesor y Asignatura"""
    profesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'profesor'},
        related_name='asignaturas_asignadas'
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='profesores_asignados'
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Profesor-Asignatura'
        verbose_name_plural = 'Profesores-Asignaturas'
        unique_together = ('profesor', 'asignatura')
    
    def __str__(self):
        return f"{self.profesor.username} → {self.asignatura.codigo}"
