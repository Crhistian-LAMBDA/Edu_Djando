#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario

print("\n=== VERIFICANDO USUARIO PERRO203 ===\n")

try:
    user = Usuario.objects.get(username='Perro203')
    print(f"Username: {user.username}")
    print(f"Nombre: {user.first_name} {user.last_name}")
    print(f"Email: {user.email}")
    print(f"Rol: {user.rol}")
    print(f"Facultad: {user.facultad} (ID: {user.facultad_id})")
    print(f"Estado: {user.estado}")
    print(f"is_active: {user.is_active}")
    print(f"is_staff: {user.is_staff}")
    
    # Verificar si cumple condiciones para aparecer en query
    print(f"\n¿Cumple rol='profesor'? {user.rol == 'profesor'}")
    print(f"¿Tiene facultad_id=3? {user.facultad_id == 3}")
    print(f"¿Cumple ambas? {user.rol == 'profesor' and user.facultad_id == 3}")
    
except Usuario.DoesNotExist:
    print("✗ Usuario Perro203 NO existe")

print("\n=== FIN ===\n")
