"""Serializers para Matrículas."""

from rest_framework import serializers

from applications.academico.models import Asignatura, PeriodoAcademico
from applications.academico.api.serializers import AsignaturaSerializer, PeriodoAcademicoSerializer

from .models import Matricula


class MatriculaSerializer(serializers.ModelSerializer):
    # Para escritura: se reciben IDs
    asignatura = serializers.PrimaryKeyRelatedField(queryset=Asignatura.objects.all())
    periodo = serializers.PrimaryKeyRelatedField(queryset=PeriodoAcademico.objects.all())
    horario = serializers.CharField(allow_blank=True, allow_null=True, required=False)

    class Meta:
        model = Matricula
        fields = '__all__'
        read_only_fields = ('fecha', 'estudiante')

    def to_representation(self, instance):
        """Mantiene compatibilidad: devuelve asignatura/periodo como objetos."""
        rep = super().to_representation(instance)
        rep['asignatura'] = AsignaturaSerializer(instance.asignatura).data if instance.asignatura_id else None
        rep['periodo'] = PeriodoAcademicoSerializer(instance.periodo).data if instance.periodo_id else None
        return rep