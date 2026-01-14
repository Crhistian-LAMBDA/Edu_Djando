"""
Configuración del admin para evaluaciones
"""
from django.contrib import admin
from applications.evaluaciones.models import Tarea, EntregaTarea


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


@admin.register(EntregaTarea)
class EntregaTareaAdmin(admin.ModelAdmin):
    list_display = ['estudiante', 'tarea', 'fecha_entrega', 'estado_entrega', 'calificacion', 'fue_tardia']
    list_filter = ['estado_entrega', 'tarea__asignatura', 'fecha_entrega']
    search_fields = ['estudiante__username', 'estudiante__first_name', 'estudiante__last_name', 'tarea__titulo']
    date_hierarchy = 'fecha_entrega'
    readonly_fields = ['fecha_entrega', 'fue_tardia']
    
    fieldsets = (
        ('Información de Entrega', {
            'fields': ('tarea', 'estudiante', 'archivo_entrega', 'comentarios_estudiante')
        }),
        ('Estado y Fechas', {
            'fields': ('estado_entrega', 'fecha_entrega', 'fue_tardia')
        }),
        ('Calificación', {
            'fields': ('calificacion', 'comentarios_docente', 'fecha_calificacion')
        }),
    )
