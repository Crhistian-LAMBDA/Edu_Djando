"""
Serializers para modelos académicos
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from applications.academico.models import (
    Facultad,
    Asignatura,
    Carrera,
    PlanCarreraAsignatura,
    ProfesorAsignatura,
    PeriodoAcademico,
)

Usuario = get_user_model()


class FacultadSerializer(serializers.ModelSerializer):
    coordinador_nombre = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Facultad
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'coordinador', 'coordinador_nombre', 'estado', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']
    
    def get_coordinador_nombre(self, obj):
        if obj.coordinador:
            return f"{obj.coordinador.first_name} {obj.coordinador.last_name}".strip() or obj.coordinador.username
        return None


class PeriodoAcademicoSerializer(serializers.ModelSerializer):
    """
    Serializer para Periodo Académico
    """
    class Meta:
        model = PeriodoAcademico
        fields = ['id', 'nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'activo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class ProfesoresAdicionalesField(serializers.PrimaryKeyRelatedField):
    """Campo personalizado para profesores adicionales con queryset filtrado"""
    def get_queryset(self):
        return Usuario.objects.filter(
            roles__tipo='profesor'
        ).distinct()


class AsignaturaSerializer(serializers.ModelSerializer):
    # Campos read-only que muestran datos relacionados
    periodo_academico_nombre = serializers.CharField(source='periodo_academico.nombre', read_only=True)
    docente_responsable_nombre = serializers.SerializerMethodField(read_only=True)
    profesores_adicionales_ids = ProfesoresAdicionalesField(
        source='profesores_adicionales',
        many=True,
        required=False,
        allow_empty=True
    )
    profesores_adicionales_nombres = serializers.SerializerMethodField(read_only=True)
    carreras = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Carrera.objects.all(),
        required=False
    )
    
    class Meta:
        model = Asignatura
        fields = [
            'id', 'nombre', 'codigo', 'descripcion', 'creditos', 'estado',
            'docente_responsable', 'docente_responsable_nombre',
            'profesores_adicionales_ids', 'profesores_adicionales_nombres',
            'periodo_academico', 'periodo_academico_nombre',
            'carreras',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']
    
    def get_docente_responsable_nombre(self, obj):
        """Retorna nombre completo del docente responsable"""
        if obj.docente_responsable:
            return f"{obj.docente_responsable.first_name} {obj.docente_responsable.last_name}".strip() or obj.docente_responsable.username
        return None
    
    def get_profesores_adicionales_nombres(self, obj):
        """Retorna nombres de profesores adicionales"""
        return [
            f"{p.first_name} {p.last_name}".strip() or p.username 
            for p in obj.profesores_adicionales.all()
        ]
    
    def validate_codigo(self, value):
        """Validar que el código sea único"""
        # Si estamos editando, excluir la asignatura actual
        asignatura_id = self.instance.id if self.instance else None
        queryset = Asignatura.objects.filter(codigo=value)
        if asignatura_id:
            queryset = queryset.exclude(id=asignatura_id)
        
        if queryset.exists():
            raise serializers.ValidationError("Este código de asignatura ya existe.")
        return value
    
    def validate_docente_responsable(self, value):
        """Validar que el docente sea realmente un docente"""
        if value and value.rol != 'profesor':
            raise serializers.ValidationError("El docente responsable debe tener rol de profesor.")
        return value


class CarreraSerializer(serializers.ModelSerializer):
    facultad_nombre = serializers.CharField(source='facultad.nombre', read_only=True)

    class Meta:
        model = Carrera
        fields = [
            'id', 'nombre', 'codigo', 'descripcion', 'nivel', 'modalidad',
            'facultad', 'facultad_nombre', 'estado', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']


class ProfesorAsignaturaSerializer(serializers.ModelSerializer):
    asignatura_nombre = serializers.CharField(source='asignatura.nombre', read_only=True)
    asignatura_codigo = serializers.CharField(source='asignatura.codigo', read_only=True)
    profesor_username = serializers.CharField(source='profesor.username', read_only=True)
    profesor_nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = ProfesorAsignatura
        fields = [
            'id', 'profesor', 'profesor_username', 'profesor_nombre_completo',
            'asignatura', 'asignatura_nombre', 'asignatura_codigo', 'fecha_asignacion'
        ]
    
    def get_profesor_nombre_completo(self, obj):
        return f"{obj.profesor.first_name} {obj.profesor.last_name}".strip()


class PlanCarreraAsignaturaSerializer(serializers.ModelSerializer):
    carrera_nombre = serializers.CharField(source='carrera.nombre', read_only=True)
    carrera_codigo = serializers.CharField(source='carrera.codigo', read_only=True)
    asignatura_nombre = serializers.CharField(source='asignatura.nombre', read_only=True)
    asignatura_codigo = serializers.CharField(source='asignatura.codigo', read_only=True)

    class Meta:
        model = PlanCarreraAsignatura
        fields = [
            'id', 'carrera', 'carrera_nombre', 'carrera_codigo',
            'asignatura', 'asignatura_nombre', 'asignatura_codigo',
            'semestre', 'es_obligatoria', 'creditos_override', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']
