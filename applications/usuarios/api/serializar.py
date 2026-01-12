from rest_framework import serializers
from django.contrib.auth import get_user_model
from applications.usuarios.models import Permiso, Rol, get_role_level
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
        from applications.usuarios.tasks import send_welcome_email
        
        password = validated_data.pop('password')

        # Seguridad: ignorar cualquier rol/estado/is_active enviados por el cliente
        validated_data.pop('rol', None)
        validated_data.pop('estado', None)
        validated_data.pop('is_active', None)
        
        # IMPORTANTE: El nuevo usuario siempre se crea INACTIVO
        validated_data['is_active'] = False
        validated_data['estado'] = 'inactivo'
        
        # Crear usuario
        usuario = Usuario.objects.create_user(
            **validated_data,
            password=password
        )

        # Asegurar que no tenga roles asignados al registrarse
        try:
            usuario.roles.clear()
        except Exception:
            pass
        
        # Enviar correo de bienvenida (pendiente de aprobación)
        try:
            send_welcome_email.delay(
                user_email=usuario.email,
                username=usuario.username,
                first_name=usuario.first_name or usuario.username,
                pending_approval=True,
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
    # `roles` se acepta en escritura como lista de strings (tipos).
    # En lectura lo inyectamos manualmente en `to_representation` para evitar
    # que DRF intente iterar el ManyRelatedManager (causa de 500 en login).
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=[c[0] for c in Rol.TIPOS_ROLES]),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    asignaturas_matriculadas = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'numero_documento',
            'rol', 'rol_display', 'roles', 'estado', 'is_active', 'is_staff', 'is_superuser',
            'facultad', 'facultad_nombre', 'carrera', 'carrera_nombre', 'asignaturas_ids',
            'asignaturas_matriculadas',
            'fecha_creacion', 'date_joined', 'last_login'
        )
        read_only_fields = (
            'id', 'fecha_creacion', 'date_joined', 'last_login'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Asegurar salida consistente: roles como lista de strings desde M2M
        try:
            data['roles'] = [r.tipo for r in instance.roles.all()]
        except Exception:
            data['roles'] = []
        return data

    def validate(self, attrs):
        request = self.context.get('request')
        user_actual = getattr(request, 'user', None) if request else None

        # Si no hay actor autenticado, no aplicamos reglas jerárquicas aquí.
        if not user_actual or not getattr(user_actual, 'is_authenticated', False):
            return attrs

        # No permitir que el usuario intente tocar roles/rol sobre sí mismo (el View ya lo bloquea, esto refuerza).
        if self.instance is not None and getattr(self.instance, 'id', None) == getattr(user_actual, 'id', None):
            if 'rol' in attrs or 'roles' in attrs:
                raise serializers.ValidationError({'roles': 'No puedes modificar tus propios roles.'})

        # Validación jerárquica HU-05 para asignación de rol legacy
        if 'rol' in attrs and attrs.get('rol'):
            target_role = attrs.get('rol')
            if not user_actual.puede_asignar_rol(target_role):
                raise serializers.ValidationError({'rol': 'No puedes asignar un rol igual o superior al tuyo.'})
            if target_role in ['super_admin', 'admin'] and user_actual.get_nivel_jerarquia() < get_role_level('super_admin'):
                raise serializers.ValidationError({'rol': 'Solo super_admin puede asignar roles admin o super_admin.'})

        # Validación jerárquica HU-05 para roles M2M
        if 'roles' in attrs:
            roles_list = attrs.get('roles') or []
            for r in roles_list:
                if not user_actual.puede_asignar_rol(r):
                    raise serializers.ValidationError({'roles': 'No puedes asignar roles iguales o superiores al tuyo.'})
                if r in ['super_admin', 'admin'] and user_actual.get_nivel_jerarquia() < get_role_level('super_admin'):
                    raise serializers.ValidationError({'roles': 'Solo super_admin puede asignar roles admin o super_admin.'})

        return attrs

    def validate_numero_documento(self, value):
        # Permitir que el propio usuario conserve su número, pero solo roles elevados pueden cambiarlo
        request = self.context.get('request')
        instance = self.instance
        if instance:
            # Si el valor no cambia, permitir
            if instance.numero_documento == value:
                return value
        # Validar unicidad
        if Usuario.objects.filter(numero_documento=value).exclude(pk=getattr(instance, 'pk', None)).exists():
            raise serializers.ValidationError("Este número de documento ya está registrado.")
        return value
    
    def update(self, instance, validated_data):
        roles_tipos = validated_data.pop('roles', None)

        # Actualización normal de campos
        instance = super().update(instance, validated_data)

        # Si se mandó `roles`, persistir en M2M
        if roles_tipos is not None:
            role_objs = list(Rol.objects.filter(tipo__in=roles_tipos))
            if len(role_objs) != len(set(roles_tipos)):
                raise serializers.ValidationError({'roles': 'Uno o más roles no existen.'})
            instance.roles.set(role_objs)

            # Sincronizar rol legacy al rol principal (más alto)
            principal = None
            for t in roles_tipos:
                if principal is None or get_role_level(t) > get_role_level(principal):
                    principal = t
            if principal:
                instance.rol = principal
                instance.save(update_fields=['rol'])

        return instance

    def get_asignaturas_ids(self, obj):
        """Obtener IDs de asignaturas asignadas al profesor"""
        if obj.rol == 'profesor':
            return list(obj.asignaturas_asignadas.values_list('asignatura_id', flat=True))
        return []

    def get_asignaturas_matriculadas(self, obj):
        """Obtener asignaturas matriculadas activas del estudiante (solo periodo activo). Nunca falla si falta info."""
        try:
            if getattr(obj, 'rol', None) != 'estudiante':
                return []
            from applications.matriculas.models import Matricula
            from applications.academico.models import PeriodoAcademico
            periodo_activo = PeriodoAcademico.objects.filter(estado='activo').order_by('-fecha_inicio').first()
            if not periodo_activo:
                return []
            matriculas = Matricula.objects.filter(estudiante=obj, periodo=periodo_activo, estado='activa').select_related('asignatura')
            result = []
            for m in matriculas:
                asignatura = getattr(m, 'asignatura', None)
                periodo = getattr(m, 'periodo', None)
                result.append({
                    'id': m.id,
                    'asignatura_id': getattr(asignatura, 'id', None),
                    'asignatura_nombre': getattr(asignatura, 'nombre', ''),
                    'asignatura_codigo': getattr(asignatura, 'codigo', ''),
                    'periodo_id': getattr(periodo, 'id', None),
                    'periodo_nombre': getattr(periodo, 'nombre', ''),
                })
            return result
        except Exception:
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
