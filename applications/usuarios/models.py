from django.contrib.auth.models import AbstractUser
from django.db import models


class Permiso(models.Model):
    """Modelo de permisos granulares para control de acceso a funcionalidades específicas"""
    MODULOS = (
        ('academico', 'Académico'),
        ('usuarios', 'Usuarios'),
        ('reportes', 'Reportes'),
        ('notificaciones', 'Notificaciones'),
    )
    
    codigo = models.CharField(
        max_length=100,
        unique=True,
        help_text='Código único del permiso (ej: crear_asignatura, calificar_tarea)'
    )
    nombre = models.CharField(
        max_length=200,
        help_text='Nombre descriptivo del permiso'
    )
    descripcion = models.TextField(
        blank=True,
        help_text='Descripción detallada del permiso'
    )
    modulo = models.CharField(
        max_length=50,
        choices=MODULOS,
        help_text='Módulo al que pertenece el permiso'
    )
    activo = models.BooleanField(
        default=True,
        help_text='Indica si el permiso está activo'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['modulo', 'codigo']
    
    def __str__(self):
        return f"{self.modulo} - {self.nombre}"


class Rol(models.Model):
    """Modelo de roles para permitir múltiples roles por usuario"""
    TIPOS_ROLES = (
        ('super_admin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('coordinador', 'Coordinador'),
        ('profesor', 'Profesor'),
        ('estudiante', 'Estudiante'),
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_ROLES,
        unique=True
    )
    descripcion = models.CharField(max_length=200, blank=True)
    permisos_asignados = models.ManyToManyField(
        Permiso,
        blank=True,
        related_name='roles',
        help_text='Permisos específicos asignados a este rol'
    )
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.get_tipo_display()
    
    def tiene_permiso(self, codigo_permiso):
        """Verifica si el rol tiene un permiso específico"""
        return self.permisos_asignados.filter(codigo=codigo_permiso, activo=True).exists()


class Usuario(AbstractUser):
    ESTADOS = (
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    )
    
    roles = models.ManyToManyField(
        Rol,
        blank=True,
        related_name='usuarios',
        help_text='Un usuario puede tener múltiples roles'
    )
    
    # Campo legacy para compatibilidad (será eliminado después)
    rol = models.CharField(
        max_length=20,
        choices=[('super_admin', 'Super Administrador'), ('admin', 'Administrador'), ('coordinador', 'Coordinador'), ('profesor', 'Profesor'), ('estudiante', 'Estudiante')],
        null=True,
        blank=True
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
    
    carrera = models.ForeignKey(
        'academico.Carrera',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudiantes',
        help_text='Carrera académica (solo para estudiantes)'
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
        roles_list = ', '.join([r.get_tipo_display() for r in self.roles.all()]) or 'Sin roles'
        return f"{self.username} - {roles_list}"
    
    def tiene_rol(self, tipo_rol):
        """Verifica si el usuario tiene un rol específico"""
        return self.roles.filter(tipo=tipo_rol).exists()
    
    def tiene_alguno_de_estos_roles(self, tipos_roles):
        """Verifica si el usuario tiene alguno de los roles especificados"""
        return self.roles.filter(tipo__in=tipos_roles).exists()
    
    def tiene_permiso(self, codigo_permiso):
        """Verifica si el usuario tiene un permiso específico a través de sus roles"""
        # Super admin siempre tiene todos los permisos
        if self.roles.filter(tipo='super_admin').exists():
            return True
        
        # Verificar si alguno de los roles del usuario tiene el permiso
        for rol in self.roles.all():
            if rol.tiene_permiso(codigo_permiso):
                return True
        return False
    
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
