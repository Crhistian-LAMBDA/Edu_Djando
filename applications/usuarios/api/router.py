from rest_framework.routers import DefaultRouter
from .view import UsuarioViewSet
from .view_academico import FacultadViewSet, AsignaturaViewSet, ProgramaViewSet, ProfesorAsignaturaViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'facultades', FacultadViewSet, basename='facultad')
router.register(r'asignaturas', AsignaturaViewSet, basename='asignatura')
router.register(r'programas', ProgramaViewSet, basename='programa')
router.register(r'profesor-asignaturas', ProfesorAsignaturaViewSet, basename='profesor-asignatura')

urlpatterns = router.urls
