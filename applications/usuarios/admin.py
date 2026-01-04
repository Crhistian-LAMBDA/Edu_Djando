from django.contrib import admin
from .models import Usuario, PasswordResetToken


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'estado', 'facultad', 'carrera', 'is_staff')
    list_filter = ('rol', 'estado', 'is_staff', 'is_superuser', 'facultad', 'carrera', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'estado')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Rol y Estado', {'fields': ('rol', 'estado')}),
        ('Asignaciones Académicas', {'fields': ('facultad', 'carrera')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'token', 'fecha_creacion', 'fecha_expiracion', 'usado')
    list_filter = ('usado', 'fecha_creacion', 'fecha_expiracion')
    search_fields = ('usuario__username', 'usuario__email', 'token')
    ordering = ('-fecha_creacion',)

