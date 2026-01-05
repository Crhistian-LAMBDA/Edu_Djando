"""
URL configuration for edu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from applications.usuarios.api.router import router as usuarios_router
from applications.academico.api.router import router as academico_router
from applications.evaluaciones.api.router import router as evaluaciones_router

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API REST - Usuarios y Auth
    path('api/', include(usuarios_router.urls)),
    # API REST - Académico
    path('api/', include(academico_router.urls)),
    # API REST - Evaluaciones
    path('api/', include(evaluaciones_router.urls)),
    
    # JWT refresh (SimpleJWT estándar)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Swagger/OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

