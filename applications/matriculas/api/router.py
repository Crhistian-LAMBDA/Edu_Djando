# router.py para Matriculas
from rest_framework.routers import DefaultRouter
from applications.matriculas.views import MatriculaViewSet

router = DefaultRouter()
router.register(r'matriculas', MatriculaViewSet, basename='matricula')

urlpatterns = router.urls