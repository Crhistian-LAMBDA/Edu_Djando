from django.contrib import admin

from .models import RecordatorioVencimiento


@admin.register(RecordatorioVencimiento)
class RecordatorioVencimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tarea', 'tipo_recordatorio', 'scheduled_for', 'sent_at', 'created_at')
    list_filter = ('tipo_recordatorio', 'sent_at')
    search_fields = ('tarea__titulo', 'tarea__asignatura__nombre', 'tarea__asignatura__codigo')
