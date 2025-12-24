from rest_framework import serializers
from applications.usuarios.models import Facultad, Asignatura, Programa, ProfesorAsignatura


class FacultadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facultad
        fields = ['id', 'nombre', 'descripcion', 'fecha_creacion']


class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'creditos', 'fecha_creacion']


class ProgramaSerializer(serializers.ModelSerializer):
    facultad_nombre = serializers.CharField(source='facultad.nombre', read_only=True)
    
    class Meta:
        model = Programa
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'facultad', 'facultad_nombre', 'fecha_creacion']


class ProfesorAsignaturaSerializer(serializers.ModelSerializer):
    asignatura_nombre = serializers.CharField(source='asignatura.nombre', read_only=True)
    asignatura_codigo = serializers.CharField(source='asignatura.codigo', read_only=True)
    
    class Meta:
        model = ProfesorAsignatura
        fields = ['id', 'profesor', 'asignatura', 'asignatura_nombre', 'asignatura_codigo', 'fecha_asignacion']
