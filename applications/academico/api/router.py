"""
Router para endpoints académicos
"""
from rest_framework.routers import DefaultRouter
from .views import FacultadViewSet, AsignaturaViewSet, ProgramaViewSet, ProfesorAsignaturaViewSet

router = DefaultRouter()
router.register(r'facultades', FacultadViewSet, basename='facultad')
router.register(r'asignaturas', AsignaturaViewSet, basename='asignatura')
router.register(r'programas', ProgramaViewSet, basename='programa')
router.register(r'profesor-asignaturas', ProfesorAsignaturaViewSet, basename='profesor-asignatura')

urlpatterns = router.urls
