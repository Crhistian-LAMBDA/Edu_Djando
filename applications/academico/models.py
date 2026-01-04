"""
Modelos académicos
"""
from django.db import models
from django.conf import settings


class PeriodoAcademico(models.Model):
    """
    Período académico (semestres, trimestres, etc.)
    Ejemplo: 2024-I, 2024-II, 2025-I
    """
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Período Académico'
        verbose_name_plural = 'Períodos Académicos'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return self.nombre


class Facultad(models.Model):
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=20, unique=True, null=True, blank=True)
    descripcion = models.TextField(blank=True, null=True)
    coordinador = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facultad_coordinador',
        help_text='Coordinador designado para esta facultad'
    )
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Facultad'
        verbose_name_plural = 'Facultades'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Asignatura(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    creditos = models.IntegerField(default=0)
    estado = models.BooleanField(default=True)  # Activa/Inactiva
    docente_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol': 'profesor'},
        related_name='asignaturas_responsable'
    )
    profesores_adicionales = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='asignaturas_adicionales',
        help_text='Profesores adicionales que enseñan esta asignatura'
    )
    periodo_academico = models.ForeignKey(
        PeriodoAcademico,
        on_delete=models.PROTECT,
        related_name='asignaturas',
        default=1
    )
    carreras = models.ManyToManyField(
        'academico.Carrera',
        through='PlanCarreraAsignatura',
        related_name='asignaturas',
        blank=True
    )
    # Relación autorreferencial para prerrequisitos
    prerrequisitos = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='asignaturas_dependientes',
        help_text='Asignaturas que son requisito para esta'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Carrera(models.Model):
    NIVEL_CHOICES = (
        ('pregrado', 'Pregrado'),
        ('posgrado', 'Posgrado'),
    )

    MODALIDAD_CHOICES = (
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('mixta', 'Mixta'),
    )

    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=30)
    descripcion = models.TextField(blank=True, null=True)
    nivel = models.CharField(max_length=15, choices=NIVEL_CHOICES)
    modalidad = models.CharField(max_length=15, choices=MODALIDAD_CHOICES)
    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.PROTECT,
        related_name='carreras'
    )
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['facultad', 'codigo'], name='uniq_carrera_codigo_por_facultad'),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class PlanCarreraAsignatura(models.Model):
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,
        related_name='planes_asignaturas'
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='planes_carrera'
    )
    semestre = models.PositiveSmallIntegerField(null=True, blank=True)
    es_obligatoria = models.BooleanField(default=True)
    creditos_override = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Plan Carrera Asignatura'
        verbose_name_plural = 'Planes Carrera Asignaturas'
        ordering = ['carrera', 'semestre']
        constraints = [
            models.UniqueConstraint(fields=['carrera', 'asignatura'], name='uniq_carrera_asignatura'),
        ]

    def __str__(self):
        return f"{self.carrera.codigo} → {self.asignatura.codigo} (sem {self.semestre or '-'} )"


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
