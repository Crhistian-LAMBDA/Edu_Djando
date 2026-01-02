"""
ViewSets para modelos académicos
"""
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from applications.academico.models import (
    Facultad,
    Asignatura,
    Carrera,
    PlanCarreraAsignatura,
    ProfesorAsignatura,
    PeriodoAcademico,
)
from applications.usuarios.tasks import send_asignatura_assignment_email
from .serializers import (
    FacultadSerializer,
    AsignaturaSerializer,
    CarreraSerializer,
    PlanCarreraAsignaturaSerializer,
    ProfesorAsignaturaSerializer,
    PeriodoAcademicoSerializer,
)
from .permissions import (
    FacultadPermission,
    CarreraPermission,
    AsignaturaPermission,
    PlanCarreraAsignaturaPermission,
)


class FacultadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Facultades
    - Super admin y admin: CRUD completo
    - Coordinador, profesor, estudiante: Solo lectura
    """
    queryset = Facultad.objects.all()
    serializer_class = FacultadSerializer
    permission_classes = [FacultadPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['nombre']


class PeriodoAcademicoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Períodos Académicos"""
    queryset = PeriodoAcademico.objects.all()
    serializer_class = PeriodoAcademicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['-fecha_inicio']


class AsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Asignaturas
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + CRUD para asignaturas de su facultad
    - Profesor, estudiante: Solo lectura
    """
    serializer_class = AsignaturaSerializer
    permission_classes = [AsignaturaPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'periodo_academico', 'carreras']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['codigo']
    
    def get_queryset(self):
        """
        Optimiza queries con select_related para evitar N+1 queries
        Filtra asignaturas según el rol del usuario
        """
        queryset = Asignatura.objects.select_related(
            'docente_responsable', 
            'periodo_academico'
        ).prefetch_related('carreras__facultad')
        
        # Verificar si el usuario es coordinador (revisar ambos campos: rol y roles)
        es_coordinador = False
        if hasattr(self.request.user, 'roles') and self.request.user.roles.exists():
            es_coordinador = self.request.user.roles.filter(tipo='coordinador').exists()
        elif self.request.user.rol == 'coordinador':
            es_coordinador = True
        
        # Coordinador solo ve asignaturas de su facultad (a través de carreras)
        if es_coordinador and hasattr(self.request.user, 'facultad') and self.request.user.facultad:
            queryset = queryset.filter(carreras__facultad=self.request.user.facultad).distinct()
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Override de create para enviar email al docente cuando se asigna
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """
        Guarda la asignatura y envía email si hay docente responsable
        """
        asignatura = serializer.save()
        self._enviar_email_docente(asignatura)
    
    def update(self, request, *args, **kwargs):
        """
        Override de update para enviar email si cambia el docente
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        docente_anterior = instance.docente_responsable
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Si cambió el docente responsable, enviar email al nuevo docente
        if instance.docente_responsable != docente_anterior:
            self._enviar_email_docente(instance)
        
        return Response(serializer.data)
    
    def _enviar_email_docente(self, asignatura):
        """
        Envía email al docente responsable de forma asíncrona
        """
        if asignatura.docente_responsable:
            send_asignatura_assignment_email.delay(
                docente_email=asignatura.docente_responsable.email,
                docente_nombre=asignatura.docente_responsable.first_name,
                asignatura_nombre=asignatura.nombre,
                asignatura_codigo=asignatura.codigo,
                periodo_nombre=asignatura.periodo_academico.nombre,
                descripcion=asignatura.descripcion or ''
            )


class ProfesorAsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar relación Profesor-Asignatura"""
    queryset = ProfesorAsignatura.objects.all()
    serializer_class = ProfesorAsignaturaSerializer
    permission_classes = [IsAuthenticated]


class CarreraViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Carreras
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + CRUD para carreras de su facultad
    - Profesor, estudiante: Solo lectura
    """
    serializer_class = CarreraSerializer
    permission_classes = [CarreraPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['facultad', 'estado', 'nivel', 'modalidad']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['nombre']
    
    def get_queryset(self):
        """Filtrar carreras según el rol del usuario"""
        queryset = Carrera.objects.select_related('facultad')
        
        # Verificar si el usuario es coordinador (revisar ambos campos: rol y roles)
        es_coordinador = False
        if hasattr(self.request.user, 'roles') and self.request.user.roles.exists():
            es_coordinador = self.request.user.roles.filter(tipo='coordinador').exists()
        elif self.request.user.rol == 'coordinador':
            es_coordinador = True
        
        # Coordinador solo ve carreras de su facultad
        if es_coordinador and hasattr(self.request.user, 'facultad') and self.request.user.facultad:
            queryset = queryset.filter(facultad=self.request.user.facultad)
        
        return queryset


class PlanCarreraAsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Planes Carrera-Asignatura
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + CRUD para planes de carreras de su facultad
    - Profesor, estudiante: Solo lectura
    """
    serializer_class = PlanCarreraAsignaturaSerializer
    permission_classes = [PlanCarreraAsignaturaPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['carrera', 'asignatura', 'semestre', 'es_obligatoria']
    search_fields = ['carrera__nombre', 'asignatura__nombre', 'asignatura__codigo']
    ordering = ['carrera', 'semestre']
    
    def get_queryset(self):
        """Filtrar planes según el rol del usuario"""
        queryset = PlanCarreraAsignatura.objects.select_related('carrera', 'asignatura')
        
        # Verificar si el usuario es coordinador (revisar ambos campos: rol y roles)
        es_coordinador = False
        if hasattr(self.request.user, 'roles') and self.request.user.roles.exists():
            es_coordinador = self.request.user.roles.filter(tipo='coordinador').exists()
        elif self.request.user.rol == 'coordinador':
            es_coordinador = True
        
        # Coordinador solo ve planes de carreras de su facultad
        if es_coordinador and hasattr(self.request.user, 'facultad') and self.request.user.facultad:
            queryset = queryset.filter(carrera__facultad=self.request.user.facultad)
        
        return queryset
