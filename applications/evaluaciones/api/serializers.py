"""
Serializers para evaluaciones
"""
from rest_framework import serializers
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from applications.evaluaciones.models import Tarea, EntregaTarea
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

        # Validar suma de pesos SOLO en creación o edición, nunca en eliminación
        # (DRF no llama validate en delete)
        asignatura = data.get('asignatura')
        peso = data.get('peso_porcentual', Decimal('0.00'))
        if asignatura and peso is not None:
            # Obtener peso total actual de la asignatura (excluyendo la tarea actual si es edición)
            peso_actual = Tarea.objects.filter(
                asignatura=asignatura
            ).exclude(
                pk=self.instance.pk if self.instance else None
            ).aggregate(
                total=Sum('peso_porcentual')
            )['total'] or Decimal('0.00')
            peso_total = peso_actual + peso
            # Permitir editar si la suma no supera 100%
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


class EntregaTareaSerializer(serializers.ModelSerializer):
    """
    Serializer para EntregaTarea con validaciones de fecha y estado
    """
    estudiante_nombre = serializers.CharField(
        source='estudiante.get_full_name', 
        read_only=True
    )
    estudiante_username = serializers.CharField(
        source='estudiante.username', 
        read_only=True
    )
    tarea_titulo = serializers.CharField(source='tarea.titulo', read_only=True)
    tarea_vencimiento = serializers.DateTimeField(
        source='tarea.fecha_vencimiento', 
        read_only=True
    )
    asignatura_nombre = serializers.CharField(
        source='tarea.asignatura.nombre', 
        read_only=True
    )
    fue_tardia = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = EntregaTarea
        fields = [
            'id', 'tarea', 'tarea_titulo', 'tarea_vencimiento',
            'asignatura_nombre', 'estudiante', 'estudiante_nombre',
            'estudiante_username', 'archivo_entrega',
            'comentarios_estudiante', 'fecha_entrega', 'estado_entrega',
            'calificacion', 'comentarios_docente', 'fecha_calificacion',
            'fue_tardia'
        ]
        read_only_fields = [
            'id', 'fecha_entrega', 'estado_entrega', 
            'calificacion', 'comentarios_docente', 'fecha_calificacion'
        ]
    
    def validate(self, data):
        """Validaciones globales"""
        tarea = data.get('tarea')
        estudiante = data.get('estudiante')
        
        # Solo validar en creación (no en actualización)
        if not self.instance:
            # Validar que la tarea esté publicada
            if tarea and tarea.estado != 'publicada':
                raise serializers.ValidationError({
                    'tarea': 'No se puede entregar una tarea que no está publicada.'
                })
            
            # Validar fecha de vencimiento
            if tarea:
                ahora = timezone.now()
                if ahora > tarea.fecha_vencimiento:
                    if not tarea.permite_entrega_tardia:
                        raise serializers.ValidationError({
                            'tarea': 'La fecha de vencimiento ya pasó y esta tarea no permite entregas tardías.'
                        })
                    else:
                        # Marcar como tardía
                        data['estado_entrega'] = 'tardia'
            
            # Validar que no exista entrega previa
            if tarea and estudiante:
                existe = EntregaTarea.objects.filter(
                    tarea=tarea,
                    estudiante=estudiante
                ).exists()
                
                if existe:
                    raise serializers.ValidationError({
                        'tarea': 'Ya has entregado esta tarea anteriormente.'
                    })
        
        return data
    
    def validate_estudiante(self, value):
        """Validar que sea un estudiante"""
        if value.rol != 'estudiante':
            raise serializers.ValidationError('Solo los estudiantes pueden entregar tareas.')
        return value
    
    def validate_archivo_entrega(self, value):
        """Validar tamaño y tipo de archivo"""
        # Validar tamaño (máximo 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('El archivo no puede superar 10MB.')
        
        # Validar extensión
        extensiones_permitidas = ['.pdf', '.doc', '.docx', '.zip', '.rar', '.txt']
        nombre = value.name.lower()
        if not any(nombre.endswith(ext) for ext in extensiones_permitidas):
            raise serializers.ValidationError(
                f'Solo se permiten archivos: {", ".join(extensiones_permitidas)}'
            )
        
        return value
