from django.contrib.auth.models import AbstractUser
from django.db import models


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
        'academico.Facultad',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administradores',
        help_text='Facultad asignada (solo para admin)'
    )
    
    programa = models.ForeignKey(
        'academico.Programa',
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
    
    def enviar_correo_recuperacion(self, token):
        """Envía correo con enlace de recuperación de contraseña usando Celery"""
        from applications.usuarios.tasks import send_password_recovery_email
        
        try:
            send_password_recovery_email.delay(
                user_email=self.email,
                first_name=self.first_name,
                token=token
            )
        except Exception as e:
            print(f"Error al encolar tarea de correo de recuperación: {str(e)}")


class PasswordResetToken(models.Model):
    """Token temporal para recuperación de contraseña"""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='reset_tokens'
    )
    token = models.CharField(max_length=100, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Token de Recuperación'
        verbose_name_plural = 'Tokens de Recuperación'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Reset token para {self.usuario.username}"
    
    def esta_expirado(self):
        from django.utils import timezone
        return timezone.now() > self.fecha_expiracion
