import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edu.settings')
django.setup()

from django.contrib.auth import get_user_model

Usuario = get_user_model()

# Verificar usuarios que podrían estar autenticados
usuarios_activos = Usuario.objects.filter(is_active=True, estado='activo')

print(f"\n{'='*100}")
print(f"USUARIOS ACTIVOS EN EL SISTEMA")
print(f"{'='*100}\n")

for u in usuarios_activos:
    roles_list = [r.tipo for r in u.roles.all()] if hasattr(u.roles, 'all') else []
    print(f"Username: {u.username:20} | Email: {u.email:30}")
    print(f"   Rol (legacy): {u.rol or 'None':15} | Roles (nuevo): {', '.join(roles_list) or 'None'}")
    if hasattr(u, 'facultad') and u.facultad:
        print(f"   Facultad: {u.facultad.nombre}")
    print()
