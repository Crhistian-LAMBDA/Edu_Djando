#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario
from applications.academico.models import Facultad

print("\n=== REPARANDO ASIGNACIÓN DE FACULTAD ===\n")

# Ver todos los profesores
print("PROFESORES EN SISTEMA:")
profs = Usuario.objects.filter(rol='profesor')
for p in profs:
    print(f"  • {p.username} ({p.first_name} {p.last_name}) → Facultad: {p.facultad or 'SIN ASIGNAR'} (ID: {p.facultad_id})")

print("\nFACULTADES DISPONIBLES:")
facs = Facultad.objects.all()
for f in facs:
    print(f"  • ID {f.id}: {f.nombre}")

# Asignar facultad a Sebas32
try:
    sebas = Usuario.objects.get(username='Sebas32')
    facultad_econ = Facultad.objects.get(id=3)
    
    print(f"\nANCES: Sebas32 tenía facultad: {sebas.facultad}")
    
    sebas.facultad = facultad_econ
    sebas.save()
    
    print(f"✓ DESPUÉS: Sebas32 ahora tiene facultad: {sebas.facultad}")
    
except Usuario.DoesNotExist:
    print("\n✗ ERROR: Usuario Sebas32 NO existe en BD")
except Facultad.DoesNotExist:
    print("\n✗ ERROR: Facultad con ID 3 NO existe")

print("\nSTATUS FINAL:")
sebas_updated = Usuario.objects.get(username='Sebas32')
print(f"  Sebas32 → Facultad ID: {sebas_updated.facultad_id}, Nombre: {sebas_updated.facultad}")

print("\n=== HECHO ===\n")
