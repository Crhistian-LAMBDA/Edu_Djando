#!/usr/bin/env python
"""
Script de prueba para validar permisos por rol
Ejecutar: python manage.py runscript test_permisos_quick
"""
import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edu.settings")
django.setup()

from django.contrib.auth import get_user_model
from applications.academico.models import Facultad, Carrera
from applications.usuarios.models import Usuario
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from applications.academico.api.views import CarreraViewSet

User = get_user_model()

print("\n" + "="*80)
print("PRUEBA RÁPIDA DE PERMISOS")
print("="*80 + "\n")

# Obtener datos existentes
facultad1 = Facultad.objects.first()
if not facultad1:
    print("ERROR: No hay facultades en la base de datos")
    sys.exit(1)

# Crear usuarios de prueba si no existen
coordinador = Usuario.objects.filter(username='test_coordinador').first()
if not coordinador:
    coordinador = Usuario.objects.create_user(
        username='test_coordinador',
        email='coord@test.com',
        password='test123',
        rol='coordinador',
        facultad=facultad1
    )
    print(f"✓ Coordinador creado: {coordinador.username}")
else:
    print(f"✓ Coordinador existente: {coordinador.username}")

# Test de acceso
print("\n[Test] Coordinador accediendo a CarreraViewSet...")

factory = APIRequestFactory()
view = CarreraViewSet.as_view({'get': 'list'})

# Request como coordinador
request = factory.get('/api/carreras/')
force_authenticate(request, user=coordinador)

# Asignar request al view
view_instance = view(request)
print(f"Status: {view_instance.status_code}")

if view_instance.status_code == 200:
    datos = view_instance.data if isinstance(view_instance.data, list) else view_instance.data.get('results', [])
    print(f"Carreras vistas: {len(datos)}")
    for carrera in datos[:3]:
        print(f"  - {carrera.get('nombre')} (facultad_id: {carrera.get('facultad')})")
    print("✓ Permisos funcionando correctamente")
else:
    print("✗ Error en permisos")

print("\n" + "="*80 + "\n")
