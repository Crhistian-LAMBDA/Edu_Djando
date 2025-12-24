from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

Usuario = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar nuevos usuarios con validaciones de seguridad
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    numero_documento = serializers.CharField(max_length=30)
    
    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'first_name', 'last_name', 'numero_documento',
            'password', 'password_confirm', 'rol', 'estado', 'is_active',
            'fecha_creacion'
        )
        extra_kwargs = {
            'is_active': {'required': False},
            'estado': {'required': False},
            'fecha_creacion': {'read_only': True},
        }
    
    def validate_email(self, value):
        """Validar que el email sea único"""
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este correo electrónico ya está registrado."
            )
        return value
    
    def validate_username(self, value):
        """Validar que el username sea único"""
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Este nombre de usuario ya existe."
            )
        return value

    def validate_numero_documento(self, value):
        """Validar que el número de documento sea único"""
        if Usuario.objects.filter(numero_documento=value).exists():
            raise serializers.ValidationError(
                "Este número de documento ya está registrado."
            )
        return value
    
    def validate_password(self, value):
        """
        Validar que la contraseña cumpla con políticas de seguridad:
        - Mínimo 8 caracteres
        - Contiene mayúsculas
        - Contiene minúsculas
        - Contiene números
        """
        if len(value) < 8:
            raise serializers.ValidationError(
                "La contraseña debe tener al menos 8 caracteres."
            )
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una mayúscula."
            )
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una minúscula."
            )
        
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )
        
        return value
    
    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        password = data.pop('password')
        password_confirm = data.pop('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError({
                'password': 'Las contraseñas no coinciden.'
            })
        
        data['password'] = password
        return data
    
    def create(self, validated_data):
        """
        Crear un nuevo usuario hasheando la contraseña y enviar email de bienvenida
        """
        from applications.usuarios.tasks import send_welcome_email
        
        password = validated_data.pop('password')
        # Si no envían estado, usar el default del modelo
        estado = validated_data.get('estado', None)
        
        # Establecer is_active en True por defecto si no se proporciona
        if 'is_active' not in validated_data:
            validated_data['is_active'] = True
        
        usuario = Usuario.objects.create_user(
            **validated_data,
            password=password
        )
        
        # Enviar correo de bienvenida asíncrono con contraseña (no bloquear registro si falla)
        try:
            send_welcome_email.delay(
                user_email=usuario.email,
                username=usuario.username,
                first_name=usuario.first_name or usuario.username,
                password=password
            )
        except Exception:
            pass
        
        return usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para lectura de usuarios (sin contraseña)
    """
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    facultad_nombre = serializers.CharField(source='facultad.nombre', read_only=True)
    programa_nombre = serializers.CharField(source='programa.nombre', read_only=True)
    asignaturas_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'numero_documento',
            'rol', 'rol_display', 'estado', 'is_active', 'is_staff', 'is_superuser',
            'facultad', 'facultad_nombre', 'programa', 'programa_nombre', 'asignaturas_ids',
            'fecha_creacion', 'date_joined', 'last_login'
        )
        read_only_fields = (
            'id', 'fecha_creacion', 'date_joined', 'last_login'
        )
    
    def get_asignaturas_ids(self, obj):
        """Obtener IDs de asignaturas asignadas al profesor"""
        if obj.rol == 'profesor':
            return list(obj.asignaturas_asignadas.values_list('asignatura_id', flat=True))
        return []


class LoginSerializer(serializers.Serializer):
    """Serializer de login: autenticación por correo y contraseña"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
