import os
from celery import Celery

# Establecer configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')

app = Celery('edu')

# Cargar configuración desde Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en todas las apps instaladas
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
