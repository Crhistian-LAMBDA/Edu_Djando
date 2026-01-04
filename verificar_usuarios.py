#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario

print("=== TODOS LOS USUARIOS CON ROL PROFESOR ===\n")
todos = Usuario.objects.filter(rol='profesor')
for u in todos:
    print(f"Username: {u.username}")
    print(f"  Nombre: {u.first_name} {u.last_name}")
    print(f"  Facultad ID: {u.facultad_id}")
    print(f"  Facultad: {u.facultad}")
    print()

print("\n=== BUSCANDO SEBAS32 ===")
try:
    sebas = Usuario.objects.get(username='Sebas32')
    print(f"✓ Encontrado")
    print(f"  Nombre: {sebas.first_name} {sebas.last_name}")
    print(f"  Rol: {sebas.rol}")
    print(f"  Facultad ID: {sebas.facultad_id}")
    print(f"  Facultad: {sebas.facultad}")
    print(f"  Estado: {sebas.estado}")
    print(f"  is_active: {sebas.is_active}")
except Usuario.DoesNotExist:
    print("✗ NO existe Sebas32")
    print("\n=== BUSCANDO POR NOMBRE ===")
    por_nombre = Usuario.objects.filter(first_name__icontains='Sebastian')
    for u in por_nombre:
        print(f"  • {u.username} - {u.first_name} {u.last_name}")
