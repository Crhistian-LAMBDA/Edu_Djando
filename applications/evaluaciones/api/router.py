"""
Router para endpoints de evaluaciones
"""

from rest_framework.routers import DefaultRouter
from django.urls import path
from applications.evaluaciones.api.views import TareaViewSet, EntregaTareaViewSet, MisTareasEstudianteView

router = DefaultRouter()
router.register(r'tareas', TareaViewSet, basename='tarea')
router.register(r'entregas', EntregaTareaViewSet, basename='entrega')

# Exportar rutas personalizadas
mis_tareas_urlpatterns = [
	path('mis-tareas/', MisTareasEstudianteView.as_view(), name='mis-tareas-estudiante'),
]
