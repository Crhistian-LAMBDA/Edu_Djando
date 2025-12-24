from django.contrib import admin
from .models import Usuario, Facultad, Asignatura, Programa, ProfesorAsignatura


@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('-fecha_creacion',)


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'creditos', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'descripcion')
    list_filter = ('creditos', 'fecha_creacion')
    ordering = ('-fecha_creacion',)


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'facultad', 'fecha_creacion')
    search_fields = ('codigo', 'nombre', 'descripcion', 'facultad__nombre')
    list_filter = ('facultad', 'fecha_creacion')
    ordering = ('-fecha_creacion',)


@admin.register(ProfesorAsignatura)
class ProfesorAsignaturaAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'asignatura', 'fecha_asignacion')
    search_fields = ('profesor__username', 'profesor__first_name', 'profesor__last_name', 'asignatura__codigo', 'asignatura__nombre')
    list_filter = ('fecha_asignacion', 'asignatura')
    ordering = ('-fecha_asignacion',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'estado', 'facultad', 'programa', 'is_staff')
    list_filter = ('rol', 'estado', 'is_staff', 'is_superuser', 'facultad', 'programa', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'estado')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Rol y Estado', {'fields': ('rol', 'estado')}),
        ('Asignaciones Académicas', {'fields': ('facultad', 'programa')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
