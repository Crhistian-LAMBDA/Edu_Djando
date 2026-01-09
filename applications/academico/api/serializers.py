"""
Serializers para modelos académicos
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import models
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




class AsignaturaSerializer(serializers.ModelSerializer):
    # Campos read-only que muestran datos relacionados
    periodo_academico_nombre = serializers.CharField(source='periodo_academico.nombre', read_only=True)
    carreras = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Carrera.objects.all(),
        required=False
    )
    # Nuevos campos para mostrar carrera y facultad
    carrera_nombre = serializers.SerializerMethodField(read_only=True)
    carrera_facultad = serializers.SerializerMethodField(read_only=True)
    carrera_id = serializers.SerializerMethodField(read_only=True)
    # Prerrequisitos
    prerrequisitos = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Asignatura.objects.all(),
        required=False
    )
    prerrequisitos_nombres = serializers.SerializerMethodField(read_only=True)
    # Semestre desde PlanCarreraAsignatura
    semestre = serializers.SerializerMethodField(read_only=True)
    profesores = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    profesores_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Asignatura
        fields = [
            'id', 'nombre', 'codigo', 'descripcion', 'creditos', 'estado',
            'periodo_academico', 'periodo_academico_nombre',
            'carreras', 'carrera_nombre', 'carrera_facultad', 'carrera_id',
            'prerrequisitos', 'prerrequisitos_nombres',
            'semestre',
            'profesores', 'profesores_info',
            'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']
    

    def get_profesores_info(self, obj):
        """Retorna la lista de profesores asociados a la asignatura mediante ProfesorAsignatura"""
        profesores = ProfesorAsignatura.objects.filter(asignatura=obj)
        return [
            {
                'id': pa.profesor.id,
                'username': pa.profesor.username,
                'nombre_completo': f"{pa.profesor.first_name} {pa.profesor.last_name}".strip(),
                'fecha_asignacion': pa.fecha_asignacion,
            }
            for pa in profesores
        ]

    def create(self, validated_data):
        profesores_ids = validated_data.pop('profesores', [])
        asignatura = super().create(validated_data)
        # Limpiar relaciones previas (por si acaso)
        ProfesorAsignatura.objects.filter(asignatura=asignatura).delete()
        for profesor_id in profesores_ids:
            ProfesorAsignatura.objects.create(asignatura=asignatura, profesor_id=profesor_id)
        return asignatura

    def update(self, instance, validated_data):
        profesores_ids = validated_data.pop('profesores', None)
        asignatura = super().update(instance, validated_data)
        if profesores_ids is not None:
            # Si la lista está vacía, elimina todas las relaciones
            ProfesorAsignatura.objects.filter(asignatura=asignatura).delete()
            for profesor_id in profesores_ids:
                ProfesorAsignatura.objects.create(asignatura=asignatura, profesor_id=profesor_id)
        return asignatura
    
    def get_carrera_nombre(self, obj):
        """Retorna el nombre de la primera carrera asociada"""
        plan = obj.planes_carrera.select_related('carrera').first()
        return plan.carrera.nombre if plan else None
    
    def get_carrera_facultad(self, obj):
        """Retorna el nombre de la facultad de la primera carrera asociada"""
        plan = obj.planes_carrera.select_related('carrera__facultad').first()
        return plan.carrera.facultad.nombre if plan and plan.carrera.facultad else None
    
    def get_carrera_id(self, obj):
        """Retorna el ID de la primera carrera asociada"""
        plan = obj.planes_carrera.select_related('carrera').first()
        return plan.carrera.id if plan else None
    
    def get_prerrequisitos_nombres(self, obj):
        """Retorna nombres y códigos de los prerrequisitos"""
        return [
            {'codigo': p.codigo, 'nombre': p.nombre}
            for p in obj.prerrequisitos.all()
        ]
    
    def get_semestre(self, obj):
        """Retorna el semestre de la primera carrera asociada"""
        plan = obj.planes_carrera.first()
        return plan.semestre if plan else None
    
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
