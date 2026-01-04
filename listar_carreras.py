import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.academico.models import Carrera

carreras = Carrera.objects.select_related('facultad').all()

print(f"\n{'='*100}")
print(f"TOTAL DE CARRERAS: {carreras.count()}")
print(f"{'='*100}\n")

for c in carreras:
    print(f"ID: {c.id:3} | Código: {c.codigo:10} | Nombre: {c.nombre:45} | Facultad: {c.facultad.nombre if c.facultad else 'Sin facultad':35} | Estado: {c.estado}")

print(f"\n{'='*100}\n")

# Buscar específicamente Ingeniería de Sistemas
ing_sistemas = carreras.filter(nombre__icontains='sistemas')
if ing_sistemas.exists():
    print("\n🔍 CARRERAS QUE CONTIENEN 'SISTEMAS':")
    for c in ing_sistemas:
        print(f"   - {c.nombre} (ID: {c.id}, Código: {c.codigo})")
else:
    print("\n❌ NO SE ENCONTRÓ NINGUNA CARRERA CON 'SISTEMAS' EN EL NOMBRE")

print()
