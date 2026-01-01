from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .serializar import UsuarioSerializer
from applications.academico.models import Asignatura, ProfesorAsignatura

Usuario = get_user_model()


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión CRUD de usuarios
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtrar queryset según permisos:
        - Para list: Super_admin ve todo, admin ve estudiantes/profesores, otros su propio perfil
        - Para acciones detalle dejamos ver todo y validamos permisos en update/destroy para
          responder 403 en lugar de 404.
        """
        user = getattr(self.request, 'user', None)

        # Sin autenticación no hay queryset
        if not user or not user.is_authenticated:
            return Usuario.objects.none()

        if self.action == 'list':
            if user.is_superuser or user.rol == 'super_admin':
                return Usuario.objects.all()
            if user.rol == 'admin':
                return Usuario.objects.filter(rol__in=['estudiante', 'profesor'])
            return Usuario.objects.filter(id=user.id)

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
        Actualizar usuario con validaciones de permiso por rol
        """
        usuario = self.get_object()
        user_actual = request.user
        
        # Verificar permisos de edición
        if usuario.id == user_actual.id:
            # El usuario puede editar su propio perfil
            pass
        elif user_actual.is_superuser or user_actual.rol == 'super_admin':
            # Super_admin puede editar a todos
            pass
        elif user_actual.rol == 'admin':
            # Admin solo puede editar estudiantes y profesores, no admins ni super_admin
            if usuario.rol not in ['estudiante', 'profesor']:
                return Response(
                    {'detail': 'No tienes permiso para editar este usuario.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Otros usuarios no pueden editar a nadie más
            return Response(
                {'detail': 'No tienes permiso para editar este usuario.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Extraer asignaturas_ids si viene en request.data (solo para profesores)
        asignaturas_ids = request.data.pop('asignaturas_ids', None)
        
        serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
        
        if serializer.is_valid():
            usuario_actualizado = serializer.save()
            
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
        Eliminar usuario con validaciones de permiso por rol
        """
        usuario = self.get_object()
        user_actual = request.user
        
        # Verificar permisos de eliminación
        if user_actual.is_superuser or user_actual.rol == 'super_admin':
            # Super_admin puede eliminar a todos
            pass
        elif user_actual.rol == 'admin':
            # Admin solo puede eliminar estudiantes y profesores, no admins ni super_admin
            if usuario.rol not in ['estudiante', 'profesor']:
                return Response(
                    {'detail': 'No tienes permiso para eliminar este usuario.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Otros usuarios no pueden eliminar a nadie
            return Response(
                {'detail': 'No tienes permiso para eliminar este usuario.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

