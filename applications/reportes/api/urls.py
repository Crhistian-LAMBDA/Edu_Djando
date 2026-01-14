from django.urls import path

from .views import ForzarReporteMensualView

urlpatterns = [
    path('mensual/forzar/', ForzarReporteMensualView.as_view(), name='forzar_reporte_mensual'),
]
