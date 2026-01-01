"""
Registro en el admin de Django
"""
from django.contrib import admin
from .models import Facultad, Asignatura, Programa, ProfesorAsignatura


@admin.register(Facultad)
class FacultadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre',)


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'creditos', 'fecha_creacion')
    search_fields = ('codigo', 'nombre')
    list_filter = ('creditos',)


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'facultad', 'fecha_creacion')
    search_fields = ('codigo', 'nombre')
    list_filter = ('facultad',)


@admin.register(ProfesorAsignatura)
class ProfesorAsignaturaAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'asignatura', 'fecha_asignacion')
    search_fields = ('profesor__username', 'asignatura__codigo')
    list_filter = ('fecha_asignacion',)
