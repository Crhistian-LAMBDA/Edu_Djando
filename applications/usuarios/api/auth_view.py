"""
ViewSet para autenticación y gestión de contraseñas
"""
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .serializar import RegistroSerializer, UsuarioSerializer, LoginSerializer
from .validators import validar_password, validar_passwords_coinciden
from .utils import generar_token_recuperacion, validar_token_recuperacion

Usuario = get_user_model()


class TokenPairSerializer(serializers.Serializer):
    """Serializer simple para documentar la respuesta de login."""
    refresh = serializers.CharField()
    access = serializers.CharField()
    usuario = UsuarioSerializer()


@extend_schema_view(
    registro=extend_schema(
        summary="Registro de usuario",
        request=RegistroSerializer,
        responses={201: UsuarioSerializer},
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Ejemplo registro",
                value={
                    "username": "demo",
                    "email": "demo@example.com",
                    "first_name": "Demo",
                    "last_name": "User",
                    "password": "Pass1234",
                    "password_confirm": "Pass1234",
                    "rol": "estudiante",
                    "estado": "activo"
                },
                request_only=True,
            )
        ],
    ),
    login=extend_schema(
        summary="Login JWT",
        request=LoginSerializer,
        responses={200: TokenPairSerializer},
        tags=["Auth"],
        examples=[
            OpenApiExample(
                "Ejemplo login",
                value={"email": "admin@example.com", "password": "Pass1234"},
                request_only=True,
            )
        ],
    ),
    cambiar_password=extend_schema(
        summary="Cambiar contraseña",
        tags=["Auth"],
    ),
    solicitar_recuperacion=extend_schema(
        summary="Solicitar recuperación de contraseña",
        tags=["Auth"],
    ),
    resetear_password=extend_schema(
        summary="Confirmar recuperación de contraseña",
        tags=["Auth"],
    ),
    validar_token=extend_schema(
        summary="Validar token de recuperación",
        tags=["Auth"],
    ),
)
class AuthViewSet(viewsets.GenericViewSet):
    """ViewSet para operaciones de autenticación"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def registro(self, request):
        """
        Registrar nuevos usuarios
        POST /api/auth/registro/
        
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
        serializer = RegistroSerializer(data=request.data)
        
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

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Autenticación por JWT
        POST /api/auth/login/

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

        # NUEVA VALIDACIÓN: Usuario debe estar activo
        if not user.is_active or user.estado == 'inactivo':
            return Response(
                {'detail': 'Tu cuenta está pendiente de aprobación por un administrador. Por favor espera.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # VALIDACIÓN: Usuario debe tener al menos un rol (M2M) o rol legacy.
        # Importante: no romper usuarios antiguos; usar helpers seguros.
        roles_tipos = []
        try:
            roles_tipos = user.get_roles_tipos()
        except Exception:
            roles_tipos = []

        if len(roles_tipos) == 0 and not getattr(user, 'rol', None):
            return Response(
                {'detail': 'Tu cuenta aún no tiene roles asignados. Por favor contacta con un administrador.'},
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
    
    @action(detail=False, methods=['post'], url_path='cambiar-password')
    def cambiar_password(self, request):
        """
        Cambiar contraseña del usuario autenticado
        POST /api/auth/cambiar-password/
        
        Body esperado:
        {
            "password_actual": "OldPass123",
            "password_nuevo": "NewPass123",
            "password_nuevo_confirm": "NewPass123"
        }
        """
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Autenticación requerida.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
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
        
        # Validar que las nuevas contraseñas coincidan
        coinciden, mensaje = validar_passwords_coinciden(password_nuevo, password_nuevo_confirm)
        if not coinciden:
            return Response({'detail': mensaje}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar política de contraseña
        valida, mensaje = validar_password(password_nuevo)
        if not valida:
            return Response({'detail': mensaje}, status=status.HTTP_400_BAD_REQUEST)
        
        # Cambiar contraseña
        usuario.set_password(password_nuevo)
        usuario.save()
        
        # Enviar correo de confirmación
        usuario.enviar_correo_cambio_password()
        
        return Response(
            {'detail': 'Contraseña actualizada exitosamente. Se envió un correo de confirmación.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='solicitar-recuperacion')
    def solicitar_recuperacion(self, request):
        """
        Solicitar recuperación de contraseña
        POST /api/auth/solicitar-recuperacion/
        
        Body:
        {
            "email": "user@example.com"
        }
        """
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'detail': 'El email es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            usuario = Usuario.objects.get(email=email)
            # Generar token y enviar correo
            token = generar_token_recuperacion(usuario)
            usuario.enviar_correo_recuperacion(token)
        except Usuario.DoesNotExist:
            # Por seguridad, no revelar si el usuario existe
            pass
        
        return Response(
            {'detail': 'Si el correo existe, recibirás un enlace de recuperación.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='aprobar-usuario')
    def aprobar_usuario(self, request):
        """
        Endpoint para que Super Admin/Admin apruebe un usuario nuevo
        POST /api/auth/aprobar-usuario/
        
        Body esperado:
        {
            "usuario_id": 5,
            "roles": ["profesor", "coordinador"],
            "facultad_id": 1
        }
        """
        # Verificar que el usuario actual es super_admin o admin
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Autenticación requerida.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not (
            request.user.is_superuser
            or request.user.tiene_alguno_de_estos_roles(['super_admin', 'admin'])
            or getattr(request.user, 'rol', None) in ['super_admin', 'admin']
        ):
            return Response(
                {'detail': 'Solo Super Admin o Admin pueden aprobar usuarios.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario_id = request.data.get('usuario_id')
        roles = request.data.get('roles', [])
        facultad_id = request.data.get('facultad_id')
        
        if not usuario_id or not roles:
            return Response(
                {'detail': 'usuario_id y roles son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Regla HU-05: no permitir asignar roles iguales/superiores al aprobador
        try:
            for r in roles:
                if not request.user.puede_asignar_rol(r):
                    return Response(
                        {'detail': 'No puedes asignar un rol igual o superior al tuyo.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except Exception:
            pass
        
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response(
                {'detail': 'Usuario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Asignar roles
        from applications.usuarios.models import Rol
        rol_objects = Rol.objects.filter(tipo__in=roles)
        usuario.roles.set(rol_objects)

        # Sincronizar rol legacy al rol principal (más alto)
        try:
            from applications.usuarios.models import get_role_level
            principal = None
            for r in roles:
                if principal is None or get_role_level(r) > get_role_level(principal):
                    principal = r
            if principal:
                usuario.rol = principal
        except Exception:
            pass
        
        # Asignar facultad si se proporciona
        if facultad_id:
            from applications.academico.models import Facultad
            try:
                facultad = Facultad.objects.get(id=facultad_id)
                usuario.facultad = facultad
            except Facultad.DoesNotExist:
                pass
        
        # Activar usuario
        usuario.is_active = True
        usuario.estado = 'activo'
        usuario.save()
        
        # Enviar correo de bienvenida
        from applications.usuarios.tasks import send_approval_welcome_email
        try:
            send_approval_welcome_email.delay(
                user_email=usuario.email,
                first_name=usuario.first_name or usuario.username,
                roles=roles
            )
        except Exception:
            pass
        
        return Response(
            {
                'detail': 'Usuario aprobado y activado exitosamente.',
                'usuario': UsuarioSerializer(usuario).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='resetear-password')
    def resetear_password(self, request):
        """
        Resetear contraseña usando el token de recuperación
        POST /api/auth/resetear-password/
        
        Body:
        {
            "token": "...",
            "password_nueva": "NewPass123",
            "password_nueva_confirm": "NewPass123"
        }
        """
        token = request.data.get('token')
        password_nueva = request.data.get('password_nueva')
        password_nueva_confirm = request.data.get('password_nueva_confirm')
        
        # Validar campos requeridos
        if not all([token, password_nueva, password_nueva_confirm]):
            return Response(
                {'error': 'Todos los campos son obligatorios'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que las contraseñas coincidan
        coinciden, mensaje = validar_passwords_coinciden(password_nueva, password_nueva_confirm)
        if not coinciden:
            return Response({'error': mensaje}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar token
        reset_token, error = validar_token_recuperacion(token)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar fortaleza de contraseña
        valida, mensaje = validar_password(password_nueva)
        if not valida:
            return Response({'error': mensaje}, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar contraseña
        usuario = reset_token.usuario
        usuario.set_password(password_nueva)
        usuario.save()
        
        # Marcar token como usado
        reset_token.usado = True
        reset_token.save()
        
        return Response(
            {'detail': 'Contraseña actualizada exitosamente'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], url_path='validar-token')
    def validar_token(self, request):
        """
        Validar si un token de recuperación es válido
        POST /api/auth/validar-token/
        
        Body:
        {
            "token": "..."
        }
        """
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reset_token, error = validar_token_recuperacion(token)
        
        if error:
            return Response(
                {
                    'valido': False,
                    'mensaje': error
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            {
                'valido': True,
                'mensaje': 'Token válido'
            },
            status=status.HTTP_200_OK
        )
