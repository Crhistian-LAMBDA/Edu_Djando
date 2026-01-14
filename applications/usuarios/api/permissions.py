"""
Permission classes personalizadas para control de acceso granular
"""
from rest_framework.permissions import BasePermission


class TienePermiso(BasePermission):
    """
    Permission class que verifica si el usuario tiene un permiso específico
    
    Uso:
        class MiViewSet(viewsets.ModelViewSet):
            permission_classes = [TienePermiso]
            permiso_requerido = 'crear_asignatura'  # Para todas las acciones
            
            # O específico por acción:
            permisos_por_accion = {
                'create': 'crear_asignatura',
                'update': 'editar_asignatura',
                'partial_update': 'editar_asignatura',
                'destroy': 'eliminar_asignatura',
                'list': 'ver_asignaturas',
                'retrieve': 'ver_asignaturas',
            }
    """
    
    def has_permission(self, request, view):
        # Usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # Permitir que el usuario edite su propio perfil (nombre, apellido, email) sin permiso especial
        if view.action in ['update', 'partial_update']:
            # Solo si está editando su propio perfil
            try:
                usuario_id = view.kwargs.get('pk')
                if usuario_id and str(request.user.id) == str(usuario_id):
                    return True
            except Exception:
                pass

        # Obtener permiso requerido
        permiso_requerido = 'NO_ENCONTRADO'  # Sentinela

        # Prioridad 1: Permisos por acción
        if hasattr(view, 'permisos_por_accion'):
            permiso_requerido = view.permisos_por_accion.get(view.action, 'NO_ENCONTRADO')

        # Prioridad 2: Permiso genérico
        if permiso_requerido == 'NO_ENCONTRADO' and hasattr(view, 'permiso_requerido'):
            permiso_requerido = view.permiso_requerido

        # Si permiso_requerido es None explícitamente, solo requiere autenticación
        if permiso_requerido is None:
            return True

        # Si no se encontró permiso en ningún lugar, denegar por seguridad
        if permiso_requerido == 'NO_ENCONTRADO':
            return False

        # Verificar si el usuario tiene el permiso
        return request.user.tiene_permiso(permiso_requerido)


class TieneAlgunPermiso(BasePermission):
    """
    Permission class que verifica si el usuario tiene al menos uno de los permisos especificados
    
    Uso:
        class MiViewSet(viewsets.ModelViewSet):
            permission_classes = [TieneAlgunPermiso]
            permisos_requeridos = ['crear_asignatura', 'editar_asignatura']
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(view, 'permisos_requeridos'):
            return False
        
        permisos = view.permisos_requeridos
        if not isinstance(permisos, (list, tuple)):
            return False
        
        # Verificar si tiene al menos uno de los permisos
        for permiso in permisos:
            if request.user.tiene_permiso(permiso):
                return True
        
        return False


class TieneTodosLosPermisos(BasePermission):
    """
    Permission class que verifica si el usuario tiene todos los permisos especificados
    
    Uso:
        class MiViewSet(viewsets.ModelViewSet):
            permission_classes = [TieneTodosLosPermisos]
            permisos_requeridos = ['ver_asignaturas', 'ver_carreras']
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(view, 'permisos_requeridos'):
            return False
        
        permisos = view.permisos_requeridos
        if not isinstance(permisos, (list, tuple)):
            return False
        
        # Verificar si tiene todos los permisos
        for permiso in permisos:
            if not request.user.tiene_permiso(permiso):
                return False
        
        return True
