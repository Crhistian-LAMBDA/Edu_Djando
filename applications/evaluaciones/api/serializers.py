"""
Serializers para evaluaciones
"""
from rest_framework import serializers
from django.db.models import Sum
from decimal import Decimal
from applications.evaluaciones.models import Tarea
from applications.academico.models import Asignatura


class TareaSerializer(serializers.ModelSerializer):
    """
    Serializer para Tarea con validaciones de pesos y fechas
    """
    asignatura_nombre = serializers.CharField(source='asignatura.nombre', read_only=True)
    asignatura_codigo = serializers.CharField(source='asignatura.codigo', read_only=True)
    peso_total_asignatura = serializers.SerializerMethodField(read_only=True)
    esta_vencida = serializers.BooleanField(read_only=True)
    esta_publicada = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Tarea
        fields = [
            'id', 'asignatura', 'asignatura_nombre', 'asignatura_codigo',
            'titulo', 'descripcion', 'tipo_tarea', 'peso_porcentual',
            'fecha_publicacion', 'fecha_vencimiento', 'estado',
            'permite_entrega_tardia', 'archivo_adjunto',
            'peso_total_asignatura', 'esta_vencida', 'esta_publicada',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_peso_total_asignatura(self, obj):
        """
        Calcula el peso total de todas las tareas de la asignatura
        """
        if not obj.asignatura_id:
            return 0
        
        total = Tarea.objects.filter(
            asignatura=obj.asignatura
        ).exclude(
            pk=obj.pk  # Excluir la tarea actual para evitar doble conteo en edición
        ).aggregate(
            total=Sum('peso_porcentual')
        )['total'] or Decimal('0.00')
        
        return float(total)
    
    def validate(self, data):
        """
        Validaciones globales
        """
        # Validar fechas
        fecha_pub = data.get('fecha_publicacion')
        fecha_venc = data.get('fecha_vencimiento')
        
        if fecha_pub and fecha_venc:
            if fecha_venc <= fecha_pub:
                raise serializers.ValidationError({
                    'fecha_vencimiento': 'La fecha de vencimiento debe ser posterior a la fecha de publicación.'
                })
        
        # Validar suma de pesos
        asignatura = data.get('asignatura')
        peso = data.get('peso_porcentual', Decimal('0.00'))
        
        if asignatura and peso:
            # Obtener peso total actual de la asignatura
            peso_actual = Tarea.objects.filter(
                asignatura=asignatura
            ).exclude(
                pk=self.instance.pk if self.instance else None
            ).aggregate(
                total=Sum('peso_porcentual')
            )['total'] or Decimal('0.00')
            
            peso_total = peso_actual + peso
            
            if peso_total > 100:
                raise serializers.ValidationError({
                    'peso_porcentual': f'El peso total supera 100% (actual: {peso_actual}%, nuevo: {peso}%, total: {peso_total}%). Excede por {peso_total - 100}%.'
                })
        
        return data
    
    def validate_titulo(self, value):
        """
        Validar que el título sea único por asignatura
        """
        if len(value.strip()) < 5:
            raise serializers.ValidationError('El título debe tener al menos 5 caracteres.')
        
        return value.strip()
    
    def validate_peso_porcentual(self, value):
        """
        Validar rango de peso
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError('El peso debe estar entre 0 y 100.')
        
        return value
