from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .serializar import RegistroSerializer, UsuarioSerializer, LoginSerializer
from .serializar_academico import (
    FacultadSerializer, AsignaturaSerializer, 
    ProgramaSerializer, ProfesorAsignaturaSerializer
)
from applications.usuarios.models import Facultad, Asignatura, Programa, ProfesorAsignatura

Usuario = get_user_model()


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios con CRUD completo y registro
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Usar RegistroSerializer para la acción de registro
        """
        if self.action == 'registro':
            return RegistroSerializer
        if self.action == 'login':
            return LoginSerializer
        return UsuarioSerializer
    
    def get_permissions(self):
        """
        Permisos específicos por acción
        """
        if self.action in ('registro', 'login'):
            return [AllowAny()]
        if self.action == 'list':
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filtrar queryset según permisos:
        - Para list: Super_admin ve todo, admin ve estudiantes/profesores, otros su propio perfil
        - Para acciones detalle dejamos ver todo y validamos permisos en update/destroy para
          responder 403 en lugar de 404.
        """
        user = getattr(self.request, 'user', None)

        # Sin autenticación no hay queryset (solo se usan en registro/login con AllowAny)
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
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def registro(self, request):
        """
        Endpoint personalizado para registrar nuevos usuarios
        POST /api/usuarios/registro/
        
        Body esperado:
        {
            "username": "newuser",
            "email": "user@example.com",
            "first_name": "Juan",
            "last_name": "Pérez",
            "password": "SecurePass123",
            "password_confirm": "SecurePass123",
            "rol": "estudiante",
            "estado": "activo"
        }
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            usuario = serializer.save()
            return Response(
                {
                    'success': True,
                    'message': 'Usuario registrado exitosamente',
                    'usuario': UsuarioSerializer(usuario).data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            {
                'success': False,
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Autenticación por JWT
        POST /api/usuarios/login/

        Body esperado:
        {
            "email": "demo@example.com",
            "password": "Pass1234"
        }
        """
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Email y password son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar usuario por correo
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Validar contraseña
        if not user.check_password(password):
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'Usuario inactivo.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'usuario': UsuarioSerializer(user).data
            },
            status=status.HTTP_200_OK
        )
    
    def create(self, request, *args, **kwargs):
        """
        Crear usuario directamente (requiere autenticación)
        """
        serializer = RegistroSerializer(data=request.data)
        
        if serializer.is_valid():
            usuario = serializer.save()
            return Response(
                UsuarioSerializer(usuario).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Obtener datos del usuario autenticado actual
        GET /api/usuarios/me/
        """
        usuario = request.user
        serializer = self.get_serializer(usuario)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def cambiar_password(self, request):
        """
        Cambiar contraseña del usuario autenticado
        POST /api/usuarios/cambiar_password/
        
        Body esperado:
        {
            "password_actual": "OldPass123",
            "password_nuevo": "NewPass123",
            "password_nuevo_confirm": "NewPass123"
        }
        """
        usuario = request.user
        password_actual = request.data.get('password_actual')
        password_nuevo = request.data.get('password_nuevo')
        password_nuevo_confirm = request.data.get('password_nuevo_confirm')
        
        if not all([password_actual, password_nuevo, password_nuevo_confirm]):
            return Response(
                {'detail': 'Todos los campos son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar contraseña actual
        if not usuario.check_password(password_actual):
            return Response(
                {'detail': 'La contraseña actual es incorrecta.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que las nuevas contraseñas coincidan
        if password_nuevo != password_nuevo_confirm:
            return Response(
                {'detail': 'Las contraseñas nuevas no coinciden.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar política de contraseña
        if len(password_nuevo) < 8:
            return Response(
                {'detail': 'La contraseña debe tener al menos 8 caracteres.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga al menos una mayúscula
        if not any(c.isupper() for c in password_nuevo):
            return Response(
                {'detail': 'La contraseña debe contener al menos una letra mayúscula.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga al menos un número
        if not any(c.isdigit() for c in password_nuevo):
            return Response(
                {'detail': 'La contraseña debe contener al menos un número.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar contraseña
        usuario.set_password(password_nuevo)
        usuario.save()
        
        # Enviar correo de confirmación
        usuario.enviar_correo_cambio_password()
        
        return Response(
            {'detail': 'Contraseña actualizada exitosamente. Se envió un correo de confirmación.'},
            status=status.HTTP_200_OK
        )
    
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

