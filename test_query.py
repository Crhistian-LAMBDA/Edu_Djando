#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario
from applications.academico.models import Carrera

# Simular la query exacta
carrera = Carrera.objects.get(id=6)
print(f'Carrera: {carrera.nombre}')
print(f'Facultad de carrera: {carrera.facultad} (ID: {carrera.facultad_id})')

# Query exacta del backend
profesores = Usuario.objects.filter(rol='profesor', facultad_id=carrera.facultad_id)
print(f'\nProfesores con facultad_id {carrera.facultad_id}:')
for p in profesores:
    print(f'  • {p.username} - {p.first_name} {p.last_name}')
print(f'Total: {profesores.count()}')
