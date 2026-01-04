#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario
from applications.academico.models import Carrera

print("\n=== VERIFICANDO ESTADO ACTUAL ===\n")

# Ver TODOS los profesores
print("TODOS LOS USUARIOS CON ROL='PROFESOR':")
profs = Usuario.objects.filter(rol='profesor')
for p in profs:
    print(f"  • {p.username} - Facultad: {p.facultad} (ID: {p.facultad_id})")

print(f"\nTotal profesores: {profs.count()}")

# Probar la query exacta de la carrera 6
carrera = Carrera.objects.get(id=6)
print(f"\nCARRERA 6: {carrera.nombre}")
print(f"  Facultad: {carrera.facultad} (ID: {carrera.facultad_id})")

profesores_carrera = Usuario.objects.filter(rol='profesor', facultad_id=carrera.facultad_id)
print(f"\n  Profesores de esa facultad:")
for p in profesores_carrera:
    print(f"    • {p.username} ({p.first_name} {p.last_name})")
print(f"  Total: {profesores_carrera.count()}")

print("\n=== FIN ===\n")
