"""
Router para endpoints académicos
"""
from rest_framework.routers import DefaultRouter
from .views import (
	FacultadViewSet,
	AsignaturaViewSet,
	CarreraViewSet,
	PlanCarreraAsignaturaViewSet,
	ProfesorAsignaturaViewSet,
	PeriodoAcademicoViewSet,
)

router = DefaultRouter()
router.register(r'periodos-academicos', PeriodoAcademicoViewSet, basename='periodo-academico')
router.register(r'facultades', FacultadViewSet, basename='facultad')
router.register(r'asignaturas', AsignaturaViewSet, basename='asignatura')
router.register(r'carreras', CarreraViewSet, basename='carrera')
router.register(r'planes-carrera-asignaturas', PlanCarreraAsignaturaViewSet, basename='plan-carrera-asignatura')
router.register(r'profesor-asignaturas', ProfesorAsignaturaViewSet, basename='profesor-asignatura')

urlpatterns = router.urls
