"""
Configuración de la app académico
"""
from django.apps import AppConfig


class AcademicoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.academico'
    verbose_name = 'Académico'
