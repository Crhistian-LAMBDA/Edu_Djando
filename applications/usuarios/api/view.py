from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .serializar import UsuarioSerializer, RolSerializer, PermisoSerializer
from .permissions import TienePermiso
from applications.academico.models import Asignatura, ProfesorAsignatura
from applications.usuarios.models import Rol, Permiso

Usuario = get_user_model()


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión CRUD de usuarios con permisos granulares
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, TienePermiso]
    
    # Definir permisos requeridos por acción
    permisos_por_accion = {
        'create': 'crear_usuario',
        'update': 'editar_usuario',
        'partial_update': 'editar_usuario',
        'destroy': 'eliminar_usuario',
        'list': 'ver_usuarios',
        'retrieve': 'ver_usuarios',
        'me': None,  # El endpoint 'me' solo requiere estar autenticado
    }
    
    def get_queryset(self):
        """
        Filtrar queryset según permisos:
        - Para list: Super_admin ve todo, admin ve estudiantes/profesores, coordinador ve docentes de su facultad
        - Para acciones detalle dejamos ver todo y delegamos la restricción a update/destroy para
          responder 403 en lugar de 404.
        - Soporte para ?carrera_id=X para filtrar docentes por facultad de una carrera específica
        """
        from django.db.models import Q
        
        user = getattr(self.request, 'user', None)

        # Sin autenticación no hay queryset
        if not user or not user.is_authenticated:
            return Usuario.objects.none()

        if self.action == 'list':
            # Parámetros de query
            rol_param = self.request.query_params.get('rol')
            carrera_id_param = self.request.query_params.get('carrera_id')
            
            # Si viene carrera_id, retornar profesores de esa facultad
            if carrera_id_param and rol_param == 'docente':
                from applications.academico.models import Carrera
                try:
                    carrera = Carrera.objects.get(id=carrera_id_param)
                    queryset = Usuario.objects.filter(
                        rol='profesor',
                        facultad_id=carrera.facultad_id
                    ).distinct()
                    return queryset
                except Carrera.DoesNotExist:
                    return Usuario.objects.none()
            
            # Filtro base según rol del usuario actual (para otros casos)
            if user.is_superuser or user.rol == 'super_admin':
                queryset = Usuario.objects.all()
            elif user.rol == 'admin':
                # Admin solo ve usuarios de su facultad
                if user.facultad:
                    queryset = Usuario.objects.filter(
                        Q(facultad=user.facultad) | Q(facultad__isnull=True)
                    )
                else:
                    queryset = Usuario.objects.filter(rol__in=['estudiante', 'profesor'])
            elif user.rol == 'coordinador':
                # Coordinador ve usuarios de su facultad
                if user.facultad:
                    queryset = Usuario.objects.filter(
                        Q(facultad=user.facultad) | Q(facultad__isnull=True)
                    )
                else:
                    queryset = Usuario.objects.filter(rol__in=['estudiante', 'profesor'])
            else:
                queryset = Usuario.objects.filter(id=user.id)
            
            # Si es coordinador pidiendo docentes, filtra por su facultad
            if rol_param == 'docente' and user.rol == 'coordinador' and hasattr(user, 'facultad') and user.facultad:
                queryset = queryset.filter(
                    Q(
                        rol='profesor',
                        facultad__isnull=True
                    ) |
                    Q(
                        rol='profesor',
                        facultad=user.facultad
                    )
                ).distinct()
            elif rol_param == 'docente':
                # Si es admin o super_admin solicitando docentes, traer todos
                queryset = queryset.filter(rol='profesor')
            
            return queryset

        # En acciones detalle devolvemos todos y delegamos la restricción a update/destroy
        return Usuario.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Obtener datos del usuario autenticado actual
        GET /api/usuarios/me/
        """
        usuario = request.user
        serializer = self.get_serializer(usuario)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        Actualizar usuario con validaciones de permiso granular
        """
        usuario = self.get_object()
        user_actual = request.user
        
        # Validación: un usuario puede editar su propio perfil aunque no tenga 'editar_usuario'
        if usuario.id != user_actual.id and not user_actual.tiene_permiso('editar_usuario'):
            return Response(
                {'detail': 'No tienes permiso para editar este usuario.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Extraer asignaturas_ids si viene en request.data (solo para profesores)
        asignaturas_ids = request.data.pop('asignaturas_ids', None)
        roles_list = request.data.pop('roles', None)
        
        serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
        
        if serializer.is_valid():
            usuario_actualizado = serializer.save()
            
            # Sincronizar estado con is_active
            if 'estado' in request.data:
                if request.data['estado'] == 'activo':
                    usuario_actualizado.is_active = True
                elif request.data['estado'] == 'inactivo':
                    usuario_actualizado.is_active = False
                usuario_actualizado.save()
            
            # Sincronizar rol legacy con tabla ManyToMany roles
            if 'rol' in request.data and request.data['rol']:
                from applications.usuarios.models import Rol
                try:
                    rol_obj = Rol.objects.get(tipo=request.data['rol'])
                    # Limpiar roles anteriores y asignar el nuevo
                    usuario_actualizado.roles.clear()
                    usuario_actualizado.roles.add(rol_obj)
                except Rol.DoesNotExist:
                    pass
            
            # Si viene lista de roles, usarla (múltiples roles)
            if roles_list:
                from applications.usuarios.models import Rol
                rol_objects = Rol.objects.filter(tipo__in=roles_list)
                usuario_actualizado.roles.set(rol_objects)
            
            # Si cambió a activo, enviar correo de bienvenida
            if 'estado' in request.data and request.data['estado'] == 'activo' and usuario_actualizado.roles.count() > 0:
                from applications.usuarios.tasks import send_approval_welcome_email
                try:
                    roles_list = [r.tipo for r in usuario_actualizado.roles.all()]
                    send_approval_welcome_email.delay(
                        user_email=usuario_actualizado.email,
                        first_name=usuario_actualizado.first_name or usuario_actualizado.username,
                        roles=roles_list
                    )
                except Exception:
                    pass
            
            # Si es profesor y se enviaron asignaturas, actualizar relación N-to-N
            if usuario_actualizado.rol == 'profesor' and asignaturas_ids is not None:
                # Eliminar asignaciones previas
                ProfesorAsignatura.objects.filter(profesor=usuario_actualizado).delete()
                
                # Crear nuevas asignaciones
                for asignatura_id in asignaturas_ids:
                    try:
                        asignatura = Asignatura.objects.get(id=asignatura_id)
                        ProfesorAsignatura.objects.create(
                            profesor=usuario_actualizado,
                            asignatura=asignatura
                        )
                    except Asignatura.DoesNotExist:
                        pass
            
            return Response(UsuarioSerializer(usuario_actualizado).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """
        Eliminar usuario con validación de permiso granular
        """
        usuario = self.get_object()
        user_actual = request.user
        
        # Validación: no permitir auto-eliminarse
        if usuario.id == user_actual.id:
            return Response(
                {'detail': 'No puedes eliminar tu propia cuenta.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de roles y sus permisos.
    Solo super_admin puede modificar permisos.
    """
    queryset = Rol.objects.all().prefetch_related('permisos_asignados')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Todos pueden ver roles, pero solo super_admin puede modificarlos"""
        return Rol.objects.all().prefetch_related('permisos_asignados')
    
    def create(self, request, *args, **kwargs):
        """Solo super_admin puede crear roles"""
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists()):
            return Response(
                {'detail': 'Solo super administradores pueden crear roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Solo super_admin puede actualizar roles"""
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists()):
            return Response(
                {'detail': 'Solo super administradores pueden modificar roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Solo super_admin puede eliminar roles"""
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists()):
            return Response(
                {'detail': 'Solo super administradores pueden eliminar roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['put'], url_path='permisos')
    def actualizar_permisos(self, request, pk=None):
        """
        Actualizar permisos de un rol específico.
        PUT /api/roles/{id}/permisos/
        Body: { "permisos_ids": [1, 2, 3, ...] }
        """
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists()):
            return Response(
                {'detail': 'Solo super administradores pueden modificar permisos.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rol = self.get_object()
        permisos_ids = request.data.get('permisos_ids', [])
        
        # Validar que los permisos existen
        permisos = Permiso.objects.filter(id__in=permisos_ids)
        if len(permisos) != len(permisos_ids):
            return Response(
                {'detail': 'Algunos permisos no existen.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar permisos
        rol.permisos_asignados.set(permisos)
        
        serializer = self.get_serializer(rol)
        return Response(serializer.data)


class PermisoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para permisos.
    Todos los usuarios autenticados pueden ver la lista de permisos.
    """
    queryset = Permiso.objects.filter(activo=True).order_by('modulo', 'codigo')
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Sin paginación para obtener todos los permisos

