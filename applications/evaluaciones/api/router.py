"""
Router para endpoints de evaluaciones
"""
from rest_framework.routers import DefaultRouter
from applications.evaluaciones.api.views import TareaViewSet

router = DefaultRouter()
router.register(r'tareas', TareaViewSet, basename='tarea')
