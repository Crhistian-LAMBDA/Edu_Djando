import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario, Rol
from applications.academico.models import Facultad

# Asignar coordinadores a facultades
# Facultad 1 → coordinador_fci
facultad = Facultad.objects.get(id=1)
usuario = Usuario.objects.get(username='coordinador_fci')
facultad.coordinador = usuario
facultad.save()
print(f'✅ {facultad.nombre} → Coordinador: {usuario.username}')

# Mostrar estado
print('\n--- Facultades y sus coordinadores ---')
for fac in Facultad.objects.all():
    coord = fac.coordinador.username if fac.coordinador else 'Sin asignar'
    print(f'{fac.nombre}: {coord}')
