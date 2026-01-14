# serializers.py para Matriculas
from rest_framework import serializers
from .models import Matricula

from applications.academico.api.serializers import AsignaturaSerializer, PeriodoAcademicoSerializer

class MatriculaSerializer(serializers.ModelSerializer):
    asignatura = AsignaturaSerializer(read_only=True)
    periodo = PeriodoAcademicoSerializer(read_only=True)
    horario = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    class Meta:
        model = Matricula
        fields = '__all__'
        read_only_fields = ('fecha', 'estudiante')