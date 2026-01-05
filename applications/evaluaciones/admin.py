"""
Configuración del admin para evaluaciones
"""
from django.contrib import admin
from applications.evaluaciones.models import Tarea


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'asignatura', 'tipo_tarea', 'peso_porcentual', 'estado', 'fecha_vencimiento']
    list_filter = ['tipo_tarea', 'estado', 'asignatura']
    search_fields = ['titulo', 'descripcion', 'asignatura__nombre', 'asignatura__codigo']
    date_hierarchy = 'fecha_publicacion'
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('asignatura', 'titulo', 'descripcion', 'tipo_tarea')
        }),
        ('Evaluación', {
            'fields': ('peso_porcentual', 'estado', 'permite_entrega_tardia')
        }),
        ('Fechas', {
            'fields': ('fecha_publicacion', 'fecha_vencimiento')
        }),
        ('Adjuntos', {
            'fields': ('archivo_adjunto',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
