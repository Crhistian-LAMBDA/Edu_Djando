"""
Utilidades para gestión de tokens de recuperación
"""
import secrets
from datetime import timedelta
from django.utils import timezone
from applications.usuarios.models import PasswordResetToken


def generar_token_recuperacion(usuario):
    """
    Genera un token de recuperación de contraseña para un usuario
    
    Args:
        usuario: Instancia del modelo Usuario
        
    Retorna:
        str: Token generado
    """
    # Generar token aleatorio
    token = secrets.token_urlsafe(32)
    
    # Eliminar tokens anteriores si existen
    PasswordResetToken.objects.filter(usuario=usuario).delete()
    
    # Crear nuevo token con expiración de 1 hora
    PasswordResetToken.objects.create(
        usuario=usuario,
        token=token,
        fecha_expiracion=timezone.now() + timedelta(hours=1)
    )
    
    return token


def validar_token_recuperacion(token):
    """
    Valida un token de recuperación
    
    Args:
        token: String del token a validar
        
    Retorna:
        tuple: (reset_token_obj o None, mensaje_error o None)
    """
    try:
        reset_token = PasswordResetToken.objects.select_related('usuario').get(token=token)
    except PasswordResetToken.DoesNotExist:
        return None, 'Token inválido'
    
    if reset_token.esta_expirado():
        return None, 'El token ha expirado'
    
    if reset_token.usado:
        return None, 'El token ya fue utilizado'
    
    return reset_token, None
