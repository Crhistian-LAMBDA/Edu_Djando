#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Usuario

sebas = Usuario.objects.get(username='Sebas32')
print(f"ANTES: rol = {sebas.rol}")
sebas.rol = 'profesor'
sebas.save()
print(f"DESPUÉS: rol = {sebas.rol}")

# Verificar
sebas_updated = Usuario.objects.get(username='Sebas32')
print(f"\nVerificación final:")
print(f"  Username: {sebas_updated.username}")
print(f"  Rol: {sebas_updated.rol}")
print(f"  Facultad: {sebas_updated.facultad}")

# Ver si aparece en la query ahora
profs = Usuario.objects.filter(rol='profesor')
print(f"\nProfesores totales: {profs.count()}")
for p in profs:
    print(f"  • {p.username} - {p.facultad}")
