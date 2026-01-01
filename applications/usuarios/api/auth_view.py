"""
ViewSet para autenticación y gestión de contraseñas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializar import RegistroSerializer, UsuarioSerializer, LoginSerializer
from .validators import validar_password, validar_passwords_coinciden
from .utils import generar_token_recuperacion, validar_token_recuperacion

Usuario = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet para operaciones de autenticación
    """
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
