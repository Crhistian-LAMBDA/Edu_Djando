#!/usr/bin/env python
"""
Script para verificar si los prerrequisitos se serializan correctamente
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
django.setup()

from applications.academico.models import Asignatura
from applications.academico.api.serializers import AsignaturaSerializer
import json

print("=" * 60)
print("Verificando prerrequisitos en BD y serialización")
print("=" * 60)

# Contar asignaturas con prerrequisitos
asigs_con_prereq = Asignatura.objects.filter(prerrequisitos__isnull=False).distinct()
print(f"\nAsignaturas con prerrequisitos: {asigs_con_prereq.count()}")

# Mostrar todas las asignaturas y sus prerrequisitos
print("\n" + "=" * 60)
print("TODAS LAS ASIGNATURAS Y PRERREQUISITOS")
print("=" * 60)

for a in Asignatura.objects.all()[:10]:
    prereqs = list(a.prerrequisitos.values_list('codigo', flat=True))
    if prereqs:
        print(f"\n✓ {a.codigo} - {a.nombre}")
        print(f"  Prerrequisitos: {prereqs}")
    else:
        print(f"\n- {a.codigo} - {a.nombre} (sin prerrequisitos)")

# Serializar y mostrar
print("\n" + "=" * 60)
print("DATOS SERIALIZADOS (primeras 3 asignaturas)")
print("=" * 60)

for a in Asignatura.objects.all()[:3]:
    s = AsignaturaSerializer(a)
    data = s.data
    print(f"\n{data.get('codigo')} - {data.get('nombre')}")
    print(f"  Semestre: {data.get('semestre')}")
    print(f"  Prerrequisitos: {data.get('prerrequisitos_nombres')}")

print("\n" + "=" * 60)
