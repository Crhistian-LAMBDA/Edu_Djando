from django.urls import path
from .views import EntregasPorGrupoAPIView

urlpatterns = [
    path('entregas-por-grupo/', EntregasPorGrupoAPIView.as_view(), name='entregas-por-grupo'),
]
