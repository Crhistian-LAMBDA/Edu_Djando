"""
Validadores para usuarios
"""
from rest_framework.response import Response
from rest_framework import status


def validar_password(password):
    """
    Valida que una contraseña cumpla con las políticas de seguridad
    
    Retorna:
        tuple: (es_valido, mensaje_error)
    """
    if len(password) < 8:
        return False, 'La contraseña debe tener al menos 8 caracteres'
    
    if not any(c.isupper() for c in password):
        return False, 'La contraseña debe contener al menos una letra mayúscula'
    
    if not any(c.isdigit() for c in password):
        return False, 'La contraseña debe contener al menos un número'
    
    return True, None


def validar_passwords_coinciden(password1, password2):
    """
    Valida que dos contraseñas coincidan
    
    Retorna:
        tuple: (coinciden, mensaje_error)
    """
    if password1 != password2:
        return False, 'Las contraseñas no coinciden'
    return True, None
