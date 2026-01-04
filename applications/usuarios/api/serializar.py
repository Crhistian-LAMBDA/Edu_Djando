from rest_framework import serializers
from django.contrib.auth import get_user_model
from applications.usuarios.models import Permiso, Rol
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
        Crear un nuevo usuario como INACTIVO y SIN ROLES asignados
        Solo Super Admin/Admin pueden activarlo y asignar roles
        """
        from applications.usuarios.tasks import send_approval_pending_email
        
        password = validated_data.pop('password')
        
        # IMPORTANTE: El nuevo usuario siempre se crea INACTIVO
        validated_data['is_active'] = False
        validated_data['estado'] = 'inactivo'
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            **validated_data,
            password=password
        )
        
        # Enviar correo avisando que está pendiente de aprobación
        try:
            send_approval_pending_email.delay(
                user_email=usuario.email,
                first_name=usuario.first_name or usuario.username
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
    carrera_nombre = serializers.CharField(source='carrera.nombre', read_only=True)
    asignaturas_ids = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'numero_documento',
            'rol', 'rol_display', 'roles', 'estado', 'is_active', 'is_staff', 'is_superuser',
            'facultad', 'facultad_nombre', 'carrera', 'carrera_nombre', 'asignaturas_ids',
            'fecha_creacion', 'date_joined', 'last_login'
        )
        read_only_fields = (
            'id', 'fecha_creacion', 'date_joined', 'last_login'
        )
    
    def get_roles(self, obj):
        """Obtener lista de roles asignados al usuario"""
        return [r.tipo for r in obj.roles.all()]
    
    def get_asignaturas_ids(self, obj):
        """Obtener IDs de asignaturas asignadas al profesor"""
        if obj.rol == 'profesor':
            return list(obj.asignaturas_asignadas.values_list('asignatura_id', flat=True))
        return []


class PermisoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Permiso"""
    class Meta:
        model = Permiso
        fields = ('id', 'codigo', 'nombre', 'descripcion', 'modulo', 'activo', 'fecha_creacion')
        read_only_fields = ('id', 'fecha_creacion')


class RolSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Rol con permisos asignados"""
    permisos = PermisoSerializer(source='permisos_asignados', many=True, read_only=True)
    permisos_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permiso.objects.all(),
        source='permisos_asignados',
        write_only=True,
        required=False
    )
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = Rol
        fields = ('id', 'tipo', 'tipo_display', 'descripcion', 'permisos', 'permisos_ids')
        read_only_fields = ('id',)


class LoginSerializer(serializers.Serializer):
    """Serializer de login: autenticación por correo y contraseña"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
