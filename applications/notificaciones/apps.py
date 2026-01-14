from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications.notificaciones'

    def ready(self):
        # Registrar signals
        from . import signals  # noqa: F401
