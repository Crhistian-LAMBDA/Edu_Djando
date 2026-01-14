from django.contrib import admin

from .models import ReporteMensual


@admin.register(ReporteMensual)
class ReporteMensualAdmin(admin.ModelAdmin):
    list_display = ('id', 'year', 'month', 'fecha_generacion', 'sent_at')
    list_filter = ('year', 'month', 'sent_at')
    search_fields = ('year', 'month')
