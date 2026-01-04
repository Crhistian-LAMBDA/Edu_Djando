import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from applications.usuarios.models import Rol, Permiso

print("=" * 80)
print("PERMISOS POR ROL")
print("=" * 80)

roles = Rol.objects.all().order_by('tipo')

for rol in roles:
    permisos = rol.permisos_asignados.filter(activo=True).order_by('modulo', 'codigo')
    
    print(f"\n{'=' * 80}")
    print(f"ROL: {rol.get_tipo_display().upper()}")
    print(f"{'=' * 80}")
    print(f"Total de permisos: {permisos.count()}\n")
    
    # Agrupar por módulo
    modulos = {}
    for permiso in permisos:
        if permiso.modulo not in modulos:
            modulos[permiso.modulo] = []
        modulos[permiso.modulo].append(permiso)
    
    for modulo, permisos_modulo in modulos.items():
        print(f"\n  📁 Módulo: {modulo.upper()}")
        print(f"  {'-' * 70}")
        for idx, permiso in enumerate(permisos_modulo, 1):
            print(f"    {idx}. {permiso.nombre}")
            print(f"       └─ Código: {permiso.codigo}")

print(f"\n{'=' * 80}")
print("FIN DEL REPORTE")
print("=" * 80)
