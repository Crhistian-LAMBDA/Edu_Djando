"""
ViewSets para evaluaciones
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from decimal import Decimal
from applications.evaluaciones.models import Tarea
from applications.evaluaciones.api.serializers import TareaSerializer
from applications.evaluaciones.api.permissions import TareaPermission
from applications.evaluaciones.tasks import enviar_notificacion_tarea


class TareaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Tareas y Exámenes
    """
    serializer_class = TareaSerializer
    permission_classes = [TareaPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asignatura', 'tipo_tarea', 'estado']
    search_fields = ['titulo', 'descripcion', 'asignatura__nombre', 'asignatura__codigo']
    ordering = ['-fecha_publicacion']
    
    def get_queryset(self):
        """
        Filtrar tareas según el rol del usuario:
        - Docentes: solo tareas de sus asignaturas
        - Coordinadores: tareas de asignaturas de su facultad
        - Admins: tareas de asignaturas de su facultad (si tiene asignada)
        - Super Admins: todas las tareas
        """
        user = self.request.user
        
        # Obtener roles
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Super Admins ven todas las tareas
        if 'super_admin' in user_roles:
            return Tarea.objects.select_related('asignatura').all()
        
        # Coordinadores ven tareas de asignaturas de su facultad
        if 'coordinador' in user_roles:
            if user.facultad:
                return Tarea.objects.select_related('asignatura').filter(
                    asignatura__carreras__facultad=user.facultad
                ).distinct()
        
        # Admins ven tareas de su facultad asignada (si tiene)
        if 'admin' in user_roles:
            if user.facultad:
                return Tarea.objects.select_related('asignatura').filter(
                    asignatura__carreras__facultad=user.facultad
                ).distinct()
            # Si no tiene facultad asignada, ver todo
            return Tarea.objects.select_related('asignatura').all()
        
        # Docentes ven solo tareas de SUS asignaturas
        return Tarea.objects.select_related('asignatura').filter(
            Q(asignatura__docente_responsable=user) | 
            Q(asignatura__profesores_adicionales=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """
        Al crear una tarea, si se publica automáticamente, notificar estudiantes
        """
        tarea = serializer.save()
        
        # Si la tarea se crea con estado 'publicada', notificar
        if tarea.estado == 'publicada':
            enviar_notificacion_tarea.delay(tarea.id)
    
    def perform_update(self, serializer):
        """
        Al actualizar, si cambia a 'publicada', notificar estudiantes
        """
        tarea_anterior = self.get_object()
        estado_anterior = tarea_anterior.estado
        
        tarea = serializer.save()
        
        # Si cambia de borrador a publicada, notificar
        if estado_anterior != 'publicada' and tarea.estado == 'publicada':
            enviar_notificacion_tarea.delay(tarea.id)
    
    @action(detail=False, methods=['get'])
    def peso_por_asignatura(self, request):
        """
        Endpoint personalizado para obtener el peso total de cada asignatura
        GET /api/tareas/peso_por_asignatura/
        """
        asignatura_id = request.query_params.get('asignatura_id')
        
        if not asignatura_id:
            return Response(
                {'error': 'Se requiere el parámetro asignatura_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        peso_total = Tarea.objects.filter(
            asignatura_id=asignatura_id
        ).aggregate(
            total=Sum('peso_porcentual')
        )['total'] or Decimal('0.00')
        
        return Response({
            'asignatura_id': asignatura_id,
            'peso_total': float(peso_total),
            'peso_disponible': float(100 - peso_total),
            'completo': peso_total == 100
        })
    
    @action(detail=True, methods=['post'])
    def publicar(self, request, pk=None):
        """
        Endpoint para publicar una tarea en borrador
        POST /api/tareas/{id}/publicar/
        """
        tarea = self.get_object()
        
        if tarea.estado == 'publicada':
            return Response(
                {'error': 'La tarea ya está publicada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if tarea.estado == 'cerrada':
            return Response(
                {'error': 'No se puede publicar una tarea cerrada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tarea.estado = 'publicada'
        tarea.save()
        
        # Notificar estudiantes
        enviar_notificacion_tarea.delay(tarea.id)
        
        return Response({
            'message': 'Tarea publicada exitosamente',
            'tarea': TareaSerializer(tarea).data
        })
    
    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Endpoint para cerrar una tarea (no acepta más entregas)
        POST /api/tareas/{id}/cerrar/
        """
        tarea = self.get_object()
        
        if tarea.estado == 'cerrada':
            return Response(
                {'error': 'La tarea ya está cerrada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tarea.estado = 'cerrada'
        tarea.save()
        
        return Response({
            'message': 'Tarea cerrada exitosamente',
            'tarea': TareaSerializer(tarea).data
        })
