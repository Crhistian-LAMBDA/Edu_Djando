from rest_framework.routers import DefaultRouter
from .view import UsuarioViewSet, RolViewSet, PermisoViewSet
from .auth_view import AuthViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'permisos', PermisoViewSet, basename='permiso')

urlpatterns = router.urls
