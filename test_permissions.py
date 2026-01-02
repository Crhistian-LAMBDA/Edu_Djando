#!/usr/bin/env python
"""
Script de prueba para validar permisos por rol

Prueba los siguientes escenarios:
1. Super admin puede CRUD todas las entidades
2. Admin puede CRUD todas las entidades
3. Coordinador puede leer todo pero solo CRUD su facultad
4. Profesor solo puede leer
5. Estudiante solo puede leer

ANTES DE EJECUTAR:
  python manage.py shell < test_permissions.py

O manualmente en Django shell:
  from django.contrib.auth import get_user_model
  from applications.academico.models import Facultad, Carrera, Asignatura, PeriodoAcademico
  ... (copiar código de aquí)
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "edu.settings")
django.setup()

from django.contrib.auth import get_user_model
from applications.academico.models import Facultad, Carrera, Asignatura, PeriodoAcademico
from applications.usuarios.models import Usuario
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from applications.academico.api.views import (
    FacultadViewSet, CarreraViewSet, AsignaturaViewSet, 
    PlanCarreraAsignaturaViewSet
)

User = get_user_model()

print("\n" + "="*80)
print("PRUEBAS DE PERMISOS - MÓDULO ACADÉMICO")
print("="*80)

# Crear datos de prueba
print("\n[1] Creando datos de prueba...")

# Crear facultades
facultad1, _ = Facultad.objects.get_or_create(
    codigo='FCI',
    defaults={'nombre': 'Facultad de Ciencias Informáticas', 'descripcion': 'Test', 'estado': True}
)
facultad2, _ = Facultad.objects.get_or_create(
    codigo='FEI',
    defaults={'nombre': 'Facultad de Electrónica e Informática', 'descripcion': 'Test', 'estado': True}
)

# Crear período académico
periodo, _ = PeriodoAcademico.objects.get_or_create(
    nombre='2025-I',
    defaults={'descripcion': 'Período I 2025', 'estado': True}
)

# Crear carreras
carrera1, _ = Carrera.objects.get_or_create(
    facultad=facultad1,
    codigo='IS',
    defaults={'nombre': 'Ingeniería de Sistemas', 'nivel': 'pregrado', 'modalidad': 'presencial', 'estado': True}
)

carrera2, _ = Carrera.objects.get_or_create(
    facultad=facultad2,
    codigo='IE',
    defaults={'nombre': 'Ingeniería Electrónica', 'nivel': 'pregrado', 'modalidad': 'presencial', 'estado': True}
)

print(f"✓ Facultad 1: {facultad1.nombre} (ID: {facultad1.id})")
print(f"✓ Facultad 2: {facultad2.nombre} (ID: {facultad2.id})")
print(f"✓ Carrera 1: {carrera1.nombre} (ID: {carrera1.id}, Facultad: {carrera1.facultad.nombre})")
print(f"✓ Carrera 2: {carrera2.nombre} (ID: {carrera2.id}, Facultad: {carrera2.facultad.nombre})")

# Crear usuarios con diferentes roles
print("\n[2] Creando usuarios de prueba...")

usuarios_config = [
    ('super_admin_user', 'super_admin', facultad1),
    ('admin_user', 'admin', None),
    ('coordinador_fci', 'coordinador', facultad1),
    ('coordinador_fei', 'coordinador', facultad2),
    ('profesor_user', 'profesor', None),
    ('estudiante_user', 'estudiante', None),
]

usuarios = {}
for username, rol, facultad in usuarios_config:
    try:
        user = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        user = Usuario.objects.create_user(
            username=username,
            email=f"{username}@test.com",
            password="testpass123",
            rol=rol,
            facultad=facultad
        )
    usuarios[username] = user
    facultad_str = f" (Facultad: {facultad.nombre})" if facultad else ""
    print(f"✓ {username}: rol={rol}{facultad_str}")

# Pruebas de permiso
print("\n[3] Testando permisos...")

factory = APIRequestFactory()

def test_facultad_view(user, username):
    """Test acceso a FacultadViewSet"""
    view = FacultadViewSet.as_view({'get': 'list'})
    request = factory.get('/api/facultades/')
    force_authenticate(request, user=user)
    response = view(request)
    
    # Test de lectura
    print(f"  {username:20} - GET /api/facultades/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test de creación
    view = FacultadViewSet.as_view({'post': 'create'})
    request = factory.post('/api/facultades/', {'nombre': 'Test', 'codigo': 'TST', 'descripcion': 'Test', 'estado': True})
    force_authenticate(request, user=user)
    response = view(request)
    puede_crear = response.status_code in [201, 400]  # 201 si crea, 400 si falla validación
    autorizado = response.status_code != 403
    print(f"  {username:20} - POST /api/facultades/: {response.status_code} {'✓ (autorizado)' if autorizado else '✗ (prohibido)'}")

def test_carrera_view(user, username):
    """Test acceso a CarreraViewSet"""
    view = CarreraViewSet.as_view({'get': 'list'})
    request = factory.get('/api/carreras/')
    force_authenticate(request, user=user)
    response = view(request)
    
    print(f"  {username:20} - GET /api/carreras/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test de creación
    view = CarreraViewSet.as_view({'post': 'create'})
    request = factory.post('/api/carreras/', {
        'nombre': 'Test',
        'codigo': 'TST',
        'facultad': facultad1.id,
        'nivel': 'pregrado',
        'modalidad': 'presencial',
        'estado': True
    })
    force_authenticate(request, user=user)
    response = view(request)
    autorizado = response.status_code != 403
    print(f"  {username:20} - POST /api/carreras/: {response.status_code} {'✓ (autorizado)' if autorizado else '✗ (prohibido)'}")

print("\n  [Facultades]")
for username in ['super_admin_user', 'admin_user', 'coordinador_fci', 'profesor_user', 'estudiante_user']:
    test_facultad_view(usuarios[username], username)

print("\n  [Carreras]")
for username in ['super_admin_user', 'admin_user', 'coordinador_fci', 'coordinador_fei', 'profesor_user']:
    test_carrera_view(usuarios[username], username)

print("\n[4] Verificando filtrado de datos por coordinador...")

# Coordinador de FCI solo debe ver carreras de FCI
coordinador = usuarios['coordinador_fci']
view = CarreraViewSet.as_view({'get': 'list'})
request = factory.get('/api/carreras/')
force_authenticate(request, user=coordinador)
response = view(request)

if response.status_code == 200:
    carreras_visibles = response.data
    facultades_visibles = set(c['facultad'] for c in carreras_visibles)
    all_own_faculty = all(f == facultad1.id for f in facultades_visibles)
    print(f"  coordinador_fci ve solo su facultad: {'✓' if all_own_faculty else '✗'}")
    print(f"    Carreras vistas: {len(carreras_visibles)}")
    for c in carreras_visibles:
        print(f"      - {c['nombre']} (facultad_id: {c['facultad']})")

print("\n" + "="*80)
print("PRUEBAS COMPLETADAS")
print("="*80 + "\n")
