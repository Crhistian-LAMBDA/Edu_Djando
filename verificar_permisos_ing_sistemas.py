import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.academico.models import Carrera
from django.contrib.auth import get_user_model

Usuario = get_user_model()

# Verificar Ingeniería de Sistemas
ing_sistemas = Carrera.objects.get(id=1)
print(f"\n{'='*100}")
print(f"INFORMACIÓN DE INGENIERÍA DE SISTEMAS")
print(f"{'='*100}\n")
print(f"ID: {ing_sistemas.id}")
print(f"Código: {ing_sistemas.codigo}")
print(f"Nombre: {ing_sistemas.nombre}")
print(f"Facultad ID: {ing_sistemas.facultad.id}")
print(f"Facultad Nombre: {ing_sistemas.facultad.nombre}")
print(f"Estado: {ing_sistemas.estado}")
print(f"Nivel: {ing_sistemas.nivel}")
print(f"Modalidad: {ing_sistemas.modalidad}")

# Verificar usuarios y sus facultades
print(f"\n{'='*100}")
print(f"USUARIOS Y SUS FACULTADES")
print(f"{'='*100}\n")

for u in Usuario.objects.filter(is_active=True, estado='activo'):
    roles_list = [r.tipo for r in u.roles.all()]
    print(f"Usuario: {u.username:20} | Rol legacy: {u.rol or 'None':15}")
    print(f"   Roles nuevos: {', '.join(roles_list) or 'None'}")
    if hasattr(u, 'facultad') and u.facultad:
        print(f"   Facultad asignada: {u.facultad.nombre} (ID: {u.facultad.id})")
        if u.facultad.id == ing_sistemas.facultad.id:
            print(f"   ✅ PUEDE VER INGENIERÍA DE SISTEMAS")
        else:
            print(f"   ❌ NO PUEDE VER INGENIERÍA DE SISTEMAS (facultad diferente)")
    else:
        print(f"   Sin facultad asignada")
    
    # Verificar si es coordinador
    es_coordinador = 'coordinador' in roles_list or u.rol == 'coordinador'
    if es_coordinador:
        print(f"   🔑 ES COORDINADOR")
    print()
