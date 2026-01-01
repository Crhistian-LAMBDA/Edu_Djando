from rest_framework.routers import DefaultRouter
from .view import UsuarioViewSet
from .auth_view import AuthViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = router.urls
