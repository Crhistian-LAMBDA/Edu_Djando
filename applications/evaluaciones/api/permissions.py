"""
Permisos personalizados para evaluaciones
"""
from rest_framework.permissions import BasePermission


class TareaPermission(BasePermission):
    """
    Permiso para Tareas:
    - Docentes pueden ver/crear/editar/eliminar tareas de SUS asignaturas
    - Coordinadores y admins pueden todo
    - Estudiantes no tienen acceso a este endpoint (ellos usan otro endpoint para ver tareas)
    """
    
    def has_permission(self, request, view):
        """
        Verificar si el usuario tiene permiso para acceder a tareas
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Obtener roles del usuario
        user_roles = []
        if hasattr(request.user, 'roles') and request.user.roles.exists():
            user_roles = [r.tipo for r in request.user.roles.all()]
        elif hasattr(request.user, 'rol'):
            user_roles = [request.user.rol]
        
        # Permitir acceso a docentes, coordinadores y admins
        roles_permitidos = ['profesor', 'docente', 'coordinador', 'admin', 'super_admin']
        return any(rol in roles_permitidos for rol in user_roles)
    
    def has_object_permission(self, request, view, obj):
        """
        Verificar si el usuario tiene permiso sobre una tarea específica
        """
        user = request.user
        
        # Obtener roles
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Super Admins pueden todo
        if 'super_admin' in user_roles:
            return True
        
        # Coordinadores pueden gestionar tareas de su facultad
        if 'coordinador' in user_roles:
            if user.facultad:
                return obj.asignatura.carreras.filter(facultad=user.facultad).exists()
        
        # Admins pueden gestionar tareas de su facultad
        if 'admin' in user_roles:
            if user.facultad:
                return obj.asignatura.carreras.filter(facultad=user.facultad).exists()
            # Si no tiene facultad asignada, puede todo
            return True
        
        # Docentes solo pueden gestionar tareas de SUS asignaturas (vía ProfesorAsignatura)
        from applications.academico.models import ProfesorAsignatura
        asignatura = obj.asignatura
        es_profesor = ProfesorAsignatura.objects.filter(
            profesor=user,
            asignatura=asignatura
        ).exists()
        return es_profesor
