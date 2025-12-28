from django.contrib.auth.models import AbstractUser
from django.db import models


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


class Usuario(AbstractUser):
    ROLES = (
        ('super_admin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('profesor', 'Profesor'),
        ('estudiante', 'Estudiante'),
    )
    
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )
    
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='estudiante'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='activo'
    )

    numero_documento = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        help_text='Número de identificación del usuario'
    )
    
    # Relaciones con entidades académicas
    facultad = models.ForeignKey(
        Facultad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administradores',
        help_text='Facultad asignada (solo para admin)'
    )
    
    programa = models.ForeignKey(
        Programa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudiantes',
        help_text='Programa académico (solo para estudiantes)'
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"
    
    def enviar_correo_cambio_password(self):
        """Envía correo de confirmación cuando se cambia la contraseña"""
        from django.core.mail import send_mail
        asunto = 'Contraseña cambiada - Colegio Django'
        mensaje = f'''
Hola {self.first_name},

Tu contraseña ha sido cambiada exitosamente en el sistema de Colegio Django.

Si no realizaste este cambio, contacta al administrador inmediatamente.

Saludos,
Sistema de Gestión Educativa - Colegio Django
        '''
        try:
            send_mail(
                asunto,
                mensaje,
                'noreply@colegio.com',
                [self.email],
                fail_silently=False
            )
        except Exception as e:
            print(f"Error enviando correo a {self.email}: {str(e)}")


class ProfesorAsignatura(models.Model):
    """Tabla intermedia para relación N-to-N entre Profesor y Asignatura"""
    profesor = models.ForeignKey(
        Usuario,
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
