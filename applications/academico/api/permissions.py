"""
Permisos granulares para módulo académico basado en roles
"""
from rest_framework import permissions


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """Solo super_admin y admin pueden crear/editar/eliminar"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin'])


class IsCoordinadorOrAdminOrSuperAdmin(permissions.BasePermission):
    """Coordinador, admin y super_admin pueden acceder"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.tiene_alguno_de_estos_roles(['coordinador', 'admin', 'super_admin'])


class IsAuthenticatedReadOnly(permissions.BasePermission):
    """Cualquier usuario autenticado puede leer"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class FacultadPermission(permissions.BasePermission):
    """
    - Super admin y admin: CRUD completo
    - Coordinador, profesor, estudiante: Solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura permitida para todos los autenticados
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para super_admin y admin
        return request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin'])


class CarreraPermission(permissions.BasePermission):
    """
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + puede editar carreras de su facultad
    - Profesor, estudiante: solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura para super_admin y admin
        if request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin']):
            return True
        
        # Coordinador puede crear/editar si tiene facultad asignada
        if request.user.tiene_rol('coordinador'):
            return request.user.facultad is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin']):
            return True
        
        # Coordinador solo puede editar carreras de su facultad
        if request.user.tiene_rol('coordinador'):
            return obj.facultad == request.user.facultad
        
        return False


class AsignaturaPermission(permissions.BasePermission):
    """
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + puede editar asignaturas de su facultad
    - Profesor, estudiante: solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura para super_admin y admin
        if request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin']):
            return True
        
        # Coordinador puede crear/editar si tiene facultad asignada
        if request.user.tiene_rol('coordinador'):
            return request.user.facultad is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin']):
            return True
        
        # Coordinador puede editar asignaturas de su facultad
        # (a través de sus carreras asociadas)
        if request.user.tiene_rol('coordinador'):
            # Verificar si la asignatura está asociada a alguna carrera de su facultad
            return obj.carreras.filter(facultad=request.user.facultad).exists()
        
        return False


class PlanCarreraAsignaturaPermission(permissions.BasePermission):
    """
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + puede crear/editar planes de carreras de su facultad
    - Profesor, estudiante: solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura permitida para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura para super_admin y admin
        if request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin']):
            return True
        
        # Coordinador puede crear/editar si tiene facultad asignada
        if request.user.tiene_rol('coordinador'):
            return request.user.facultad is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin']):
            return True
        
        # Coordinador solo puede editar planes de carreras de su facultad
        if request.user.tiene_rol('coordinador'):
            return obj.carrera.facultad == request.user.facultad
        
        return False
