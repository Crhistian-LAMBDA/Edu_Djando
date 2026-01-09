"""
Registro en el admin de Django
"""
from django.contrib import admin
from .models import Facultad, Asignatura, Carrera, PlanCarreraAsignatura, ProfesorAsignatura, PeriodoAcademico

# Registrar PeriodoAcademico en el admin
@admin.register(PeriodoAcademico)
class PeriodoAcademicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'activo', 'fecha_creacion')
    search_fields = ('nombre',)
    list_filter = ('activo',)


@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'coordinador', 'estado', 'fecha_creacion')
    search_fields = ('nombre', 'codigo', 'coordinador__username')
    list_filter = ('estado',)
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion')
        }),
        ('Gestión', {
            'fields': ('coordinador', 'estado')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'creditos', 'fecha_creacion')
    search_fields = ('codigo', 'nombre')
    list_filter = ('creditos',)


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'facultad', 'nivel', 'modalidad', 'estado', 'fecha_creacion')
    search_fields = ('codigo', 'nombre')
    list_filter = ('facultad', 'nivel', 'modalidad', 'estado')


@admin.register(PlanCarreraAsignatura)
class PlanCarreraAsignaturaAdmin(admin.ModelAdmin):
    list_display = ('carrera', 'asignatura', 'semestre', 'es_obligatoria', 'fecha_creacion')
    search_fields = ('carrera__nombre', 'carrera__codigo', 'asignatura__nombre', 'asignatura__codigo')
    list_filter = ('semestre', 'es_obligatoria', 'carrera__facultad')


@admin.register(ProfesorAsignatura)
class ProfesorAsignaturaAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'asignatura', 'fecha_asignacion')
    search_fields = ('profesor__username', 'asignatura__codigo')
    list_filter = ('fecha_asignacion',)
