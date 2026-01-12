from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
class MisTareasEstudianteView(APIView):
    """
    Endpoint profesional para que el estudiante vea solo tareas de materias con horario asignado.
    GET /api/mis-tareas/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # Solo estudiantes
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        if 'estudiante' not in user_roles:
            return Response({'detail': 'Solo estudiantes pueden acceder a este endpoint.'}, status=403)

        from applications.matriculas.models import Matricula
        from applications.evaluaciones.models import Tarea
        from applications.evaluaciones.api.serializers import TareaSerializer

        # IDs de asignaturas con matrícula y horario asignado
        asignaturas_ids = Matricula.objects.filter(
            estudiante=user,
            horario__isnull=False
        ).exclude(horario='').values_list('asignatura_id', flat=True)

        tareas = Tarea.objects.select_related('asignatura').filter(
            asignatura_id__in=asignaturas_ids
        ).distinct()

        serializer = TareaSerializer(tareas, many=True)
        return Response(serializer.data)


class MisCalificacionesEstudianteView(APIView):
    """
    Resumen de calificaciones del estudiante por asignatura.
    GET /api/mis-calificaciones/

    Retorna (por asignatura matriculada con horario):
    - asignatura + docentes + horario
    - tareas (peso) + calificación del estudiante (si existe)
    - total ponderado y métricas para visualización
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Solo estudiantes
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        if 'estudiante' not in user_roles:
            return Response({'detail': 'Solo estudiantes pueden acceder a este endpoint.'}, status=403)

        from django.db.models import Prefetch
        from applications.matriculas.models import Matricula
        from applications.evaluaciones.models import Tarea, EntregaTarea
        from applications.academico.models import ProfesorAsignatura

        objetivo_aprobacion = 60.0

        matriculas = (
            Matricula.objects
            .select_related('asignatura', 'periodo')
            .filter(estudiante=user, horario__isnull=False)
            .exclude(horario='')
        )

        asignaturas_ids = list(matriculas.values_list('asignatura_id', flat=True))
        if not asignaturas_ids:
            return Response({
                'objetivo_aprobacion': objetivo_aprobacion,
                'asignaturas': [],
            })

        tareas = (
            Tarea.objects
            .select_related('asignatura')
            .filter(asignatura_id__in=asignaturas_ids)
        )
        tareas_por_asignatura = {}
        for t in tareas:
            tareas_por_asignatura.setdefault(t.asignatura_id, []).append(t)

        entregas = EntregaTarea.objects.filter(
            estudiante=user,
            tarea__asignatura_id__in=asignaturas_ids,
        )
        entregas_por_tarea = {e.tarea_id: e for e in entregas}

        profesores = (
            ProfesorAsignatura.objects
            .select_related('profesor', 'asignatura')
            .filter(asignatura_id__in=asignaturas_ids)
        )
        profesores_por_asignatura = {}
        for pa in profesores:
            profesores_por_asignatura.setdefault(pa.asignatura_id, []).append(pa.profesor)

        asignaturas_payload = []
        for m in matriculas:
            asig_id = m.asignatura_id

            docentes = profesores_por_asignatura.get(asig_id, [])
            docentes_info = [
                {
                    'id': d.id,
                    'nombre': (d.get_full_name() or d.username).strip(),
                    'email': getattr(d, 'email', None),
                }
                for d in docentes
            ]

            tareas_list = tareas_por_asignatura.get(asig_id, [])
            tareas_payload = []

            nota_acumulada = 0.0
            peso_calificado = 0.0
            peso_total = 0.0

            for t in tareas_list:
                peso = float(getattr(t, 'peso_porcentual', 0) or 0)
                peso_total += peso

                entrega = entregas_por_tarea.get(t.id)
                calificacion = None
                if entrega and entrega.calificacion is not None:
                    calificacion = float(entrega.calificacion)
                    peso_calificado += peso
                    nota_acumulada += calificacion * (peso / 100.0)

                tareas_payload.append({
                    'id': t.id,
                    'titulo': t.titulo,
                    'descripcion': t.descripcion,
                    'tipo_tarea': t.tipo_tarea,
                    'estado': t.estado,
                    'peso_porcentual': peso,
                    'fecha_publicacion': t.fecha_publicacion,
                    'fecha_vencimiento': t.fecha_vencimiento,
                    'archivo_adjunto': t.archivo_adjunto.url if getattr(t, 'archivo_adjunto', None) else None,
                    'entrega': {
                        'id': entrega.id,
                        'estado_entrega': entrega.estado_entrega,
                        'calificacion': calificacion,
                        'fecha_calificacion': entrega.fecha_calificacion,
                    } if entrega else None,
                })

            peso_restante = max(0.0, 100.0 - peso_calificado)
            requerido_en_restante = None
            if peso_restante > 0:
                requerido_en_restante = (objetivo_aprobacion - nota_acumulada) / (peso_restante / 100.0)
                if requerido_en_restante < 0:
                    requerido_en_restante = 0.0

            asignaturas_payload.append({
                'matricula_id': m.id,
                'periodo': {
                    'id': m.periodo_id,
                    'nombre': str(m.periodo),
                },
                'asignatura': {
                    'id': m.asignatura_id,
                    'codigo': m.asignatura.codigo,
                    'nombre': m.asignatura.nombre,
                },
                'horario': m.horario,
                'docentes': docentes_info,
                'tareas': tareas_payload,
                'resumen': {
                    'nota_actual_ponderada': round(nota_acumulada, 2),
                    'peso_calificado': round(peso_calificado, 2),
                    'peso_restante': round(peso_restante, 2),
                    'requerido_promedio_en_restante_para_ganar': round(requerido_en_restante, 2) if requerido_en_restante is not None else None,
                    'peso_total_tareas_asignatura': round(peso_total, 2),
                },
            })

        return Response({
            'objetivo_aprobacion': objetivo_aprobacion,
            'asignaturas': asignaturas_payload,
        })


class StaffCalificacionesPorAsignaturaView(APIView):
    """
    Vista para roles staff (profesor/docente/coordinador/admin/super_admin)
    que lista, por asignatura con docente asignado, los estudiantes matriculados
    y su estado de calificaciones (ponderado + por tarea).

    GET /api/staff-calificaciones/?periodo_id=<opcional>

    Reglas clave:
    - La lista de asignaturas se deriva de ProfesorAsignatura ("se crea" al asignar docente).
    - Si se destituye al docente, deja de aparecer (para ese docente; y en global si no queda ninguno).
    - La asignatura aparece aunque no tenga estudiantes matriculados (lista vacía).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]

        if getattr(user, 'is_superuser', False) and 'super_admin' not in user_roles:
            user_roles.append('super_admin')

        allowed_roles = {'profesor', 'docente', 'coordinador', 'admin', 'super_admin'}
        if not (set(user_roles) & allowed_roles):
            return Response({'detail': 'No tienes permisos para ver calificaciones del staff.'}, status=403)

        from applications.academico.models import PeriodoAcademico, ProfesorAsignatura, Asignatura
        from applications.matriculas.models import Matricula
        from applications.evaluaciones.models import Tarea, EntregaTarea

        periodo_id = request.query_params.get('periodo_id')
        if periodo_id:
            periodo = PeriodoAcademico.objects.filter(id=periodo_id).first()
        else:
            periodo = PeriodoAcademico.objects.filter(activo=True).first()

        if not periodo:
            return Response({'detail': 'No hay periodo académico válido (activo o periodo_id).'}, status=400)

        pa_qs = (
            ProfesorAsignatura.objects
            .select_related('asignatura', 'profesor')
            .filter(asignatura__periodo_academico=periodo)
        )

        # Alcance por rol (mismo criterio que otras vistas del proyecto)
        if 'super_admin' in user_roles:
            pass
        elif 'coordinador' in user_roles or 'admin' in user_roles:
            facultad = getattr(user, 'facultad', None)
            if not facultad:
                pa_qs = pa_qs.none()
            else:
                pa_qs = pa_qs.filter(asignatura__carreras__facultad=facultad).distinct()
        elif any(r in user_roles for r in ['profesor', 'docente']):
            pa_qs = pa_qs.filter(profesor=user)

        asignaturas_ids = list(pa_qs.values_list('asignatura_id', flat=True).distinct())
        if not asignaturas_ids:
            return Response({
                'periodo': {'id': periodo.id, 'nombre': str(periodo)},
                'asignaturas': [],
            })

        # Docentes por asignatura (para chips en UI) - deduplicado
        profesores_por_asignatura = {}
        for pa in pa_qs:
            bucket = profesores_por_asignatura.setdefault(pa.asignatura_id, {})
            bucket[pa.profesor_id] = pa.profesor

        # Asignaturas ordenadas
        asignaturas_qs = Asignatura.objects.filter(id__in=asignaturas_ids).order_by('codigo', 'nombre')
        asignaturas_orden = list(asignaturas_qs)

        # Tareas por asignatura
        tareas = (
            Tarea.objects
            .select_related('asignatura')
            .filter(asignatura_id__in=asignaturas_ids)
            .order_by('fecha_publicacion', 'id')
        )
        tareas_por_asignatura = {}
        for t in tareas:
            tareas_por_asignatura.setdefault(t.asignatura_id, []).append(t)

        # Matrículas del periodo (estudiantes matriculados por asignatura)
        matriculas = (
            Matricula.objects
            .select_related('estudiante', 'estudiante__carrera', 'asignatura', 'periodo')
            .filter(periodo=periodo, asignatura_id__in=asignaturas_ids)
            .distinct()
        )

        matriculas_por_asignatura = {}
        estudiante_ids = set()
        for m in matriculas:
            matriculas_por_asignatura.setdefault(m.asignatura_id, []).append(m)
            estudiante_ids.add(m.estudiante_id)

        # Entregas/calificaciones relevantes (tarea + estudiante)
        entregas_por_estudiante_tarea = {}
        if estudiante_ids:
            entregas = (
                EntregaTarea.objects
                .select_related('tarea')
                .filter(
                    estudiante_id__in=list(estudiante_ids),
                    tarea__asignatura_id__in=asignaturas_ids,
                )
            )
            for e in entregas:
                entregas_por_estudiante_tarea[(e.estudiante_id, e.tarea_id)] = (
                    float(e.calificacion) if e.calificacion is not None else None
                )

        asignaturas_payload = []
        for asig in asignaturas_orden:
            asig_id = asig.id
            docentes = list(profesores_por_asignatura.get(asig_id, {}).values())
            docentes_info = [
                {
                    'id': d.id,
                    'nombre': (d.get_full_name() or d.username).strip(),
                    'email': getattr(d, 'email', None),
                }
                for d in docentes
            ]

            tareas_list = tareas_por_asignatura.get(asig_id, [])
            tareas_payload = [
                {
                    'id': t.id,
                    'titulo': t.titulo,
                    'tipo_tarea': t.tipo_tarea,
                    'estado': t.estado,
                    'peso_porcentual': float(getattr(t, 'peso_porcentual', 0) or 0),
                }
                for t in tareas_list
            ]

            estudiantes_payload = []
            for m in matriculas_por_asignatura.get(asig_id, []):
                est = m.estudiante

                nota_acumulada = 0.0
                peso_calificado = 0.0

                calificaciones_por_tarea = {}
                for t in tareas_list:
                    peso = float(getattr(t, 'peso_porcentual', 0) or 0)
                    cal = entregas_por_estudiante_tarea.get((m.estudiante_id, t.id))
                    calificaciones_por_tarea[str(t.id)] = cal
                    if cal is not None:
                        peso_calificado += peso
                        nota_acumulada += cal * (peso / 100.0)

                peso_restante = max(0.0, 100.0 - peso_calificado)

                carrera = getattr(est, 'carrera', None)
                carrera_info = None
                if carrera:
                    carrera_info = {
                        'id': getattr(carrera, 'id', None),
                        'nombre': str(carrera),
                    }

                estudiantes_payload.append({
                    'id': est.id,
                    'nombre': (est.get_full_name() or est.username).strip(),
                    'username': est.username,
                    'email': getattr(est, 'email', None),
                    'carrera': carrera_info,
                    'matricula_id': m.id,
                    'resumen': {
                        'nota_actual_ponderada': round(nota_acumulada, 2),
                        'peso_calificado': round(peso_calificado, 2),
                        'peso_restante': round(peso_restante, 2),
                    },
                    'calificaciones_por_tarea': calificaciones_por_tarea,
                })

            estudiantes_payload.sort(key=lambda x: ((x.get('nombre') or '').lower(), (x.get('username') or '').lower()))

            asignaturas_payload.append({
                'periodo': {'id': periodo.id, 'nombre': str(periodo)},
                'asignatura': {
                    'id': asig_id,
                    'codigo': asig.codigo,
                    'nombre': asig.nombre,
                },
                'docentes': docentes_info,
                'tareas': tareas_payload,
                'estudiantes': estudiantes_payload,
            })

        return Response({
            'periodo': {'id': periodo.id, 'nombre': str(periodo)},
            'asignaturas': asignaturas_payload,
        })
"""
ViewSets para evaluaciones
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.utils import timezone
from decimal import Decimal
from applications.evaluaciones.models import Tarea, EntregaTarea
from applications.evaluaciones.api.serializers import TareaSerializer, EntregaTareaSerializer
from applications.evaluaciones.api.permissions import TareaPermission
from applications.evaluaciones.tasks import (
    enviar_notificacion_tarea,
    notificar_docente_nueva_entrega,
    notificar_estudiante_calificacion,
)


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

    def _assert_pesos_total_100_para_publicar(self, *, asignatura, exclude_tarea_id=None, peso_nuevo=None):
        """Exige que el total de pesos de la asignatura sea exactamente 100% al publicar."""
        total_actual = (
            Tarea.objects.filter(asignatura=asignatura)
            .exclude(pk=exclude_tarea_id)
            .aggregate(total=Sum('peso_porcentual'))
            .get('total')
        ) or Decimal('0.00')

        total = total_actual
        if peso_nuevo is not None:
            total = total_actual + (peso_nuevo or Decimal('0.00'))

        total_q = total.quantize(Decimal('0.01'))
        if total_q != Decimal('100.00'):
            raise ValidationError({
                'peso_porcentual': (
                    f'Para publicar, el total de pesos de la asignatura debe ser 100%. '
                    f'Actualmente suma {total_q}%.'
                )
            })

    def _count_estudiantes_notificados(self, tarea):
        """Cuenta cuántos estudiantes serían notificados (matriculados con horario no vacío)."""
        from applications.matriculas.models import Matricula

        return (
            Matricula.objects.filter(
                asignatura=tarea.asignatura,
                horario__isnull=False,
            )
            .exclude(horario='')
            .values('estudiante_id')
            .distinct()
            .count()
        )

    def create(self, request, *args, **kwargs):
        """Extiende la respuesta de creación para incluir `estudiantes_notificados` si se crea publicada."""
        response = super().create(request, *args, **kwargs)
        try:
            if getattr(response, 'status_code', None) in (200, 201):
                estado = None
                tarea_id = None
                if isinstance(getattr(response, 'data', None), dict):
                    estado = response.data.get('estado')
                    tarea_id = response.data.get('id')

                if estado == 'publicada' and tarea_id:
                    tarea = Tarea.objects.select_related('asignatura').filter(id=tarea_id).first()
                    if tarea:
                        response.data['estudiantes_notificados'] = self._count_estudiantes_notificados(tarea)
        except Exception:
            # No romper el flujo si falla el conteo
            pass

        return response
    
    def get_queryset(self):
        """
        Filtrar tareas según el rol del usuario:
        - Docentes: solo tareas de sus asignaturas
        - Coordinadores: tareas de asignaturas de su facultad
        - Admins: tareas de asignaturas de su facultad (si tiene asignada)
        - Super Admins: todas las tareas
        - Estudiantes: solo tareas de asignaturas donde tiene matrícula y horario guardado
        """
        user = self.request.user
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]

        if getattr(user, 'is_superuser', False) and 'super_admin' not in user_roles:
            user_roles.append('super_admin')

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
            return Tarea.objects.select_related('asignatura').none()

        # Docentes ven solo tareas de SUS asignaturas (vía ProfesorAsignatura)
        if any(rol in ['profesor', 'docente'] for rol in user_roles):
            from applications.academico.models import ProfesorAsignatura
            asignaturas_ids = ProfesorAsignatura.objects.filter(
                profesor=user
            ).values_list('asignatura_id', flat=True)
            return Tarea.objects.select_related('asignatura').filter(
                asignatura_id__in=asignaturas_ids
            ).distinct()

        # Estudiantes: solo tareas de asignaturas donde tiene matrícula y horario guardado
        if 'estudiante' in user_roles:
            from applications.matriculas.models import Matricula
            # Buscar asignaturas donde el estudiante tiene matrícula y horario no vacío
            asignaturas_ids = Matricula.objects.filter(
                estudiante=user,
                horario__isnull=False
            ).exclude(horario='').values_list('asignatura_id', flat=True)
            return Tarea.objects.select_related('asignatura').filter(
                asignatura_id__in=asignaturas_ids
            ).distinct()

        # Por defecto, no mostrar tareas
        return Tarea.objects.none()
    
    def perform_create(self, serializer):
        """
        Al crear una tarea, si se publica automáticamente, notificar estudiantes
        """
        estado = serializer.validated_data.get('estado')
        if estado == 'publicada':
            asignatura = serializer.validated_data.get('asignatura')
            peso = serializer.validated_data.get('peso_porcentual')
            self._assert_pesos_total_100_para_publicar(asignatura=asignatura, peso_nuevo=peso)

        tarea = serializer.save()

        if tarea.estado == 'publicada':
            enviar_notificacion_tarea.delay(tarea.id)
    
    def perform_update(self, serializer):
        """
        Al actualizar, si cambia a 'publicada', notificar estudiantes
        """
        tarea_anterior = self.get_object()
        estado_anterior = tarea_anterior.estado

        nuevo_estado = serializer.validated_data.get('estado', tarea_anterior.estado)
        if estado_anterior != 'publicada' and nuevo_estado == 'publicada':
            asignatura = serializer.validated_data.get('asignatura', tarea_anterior.asignatura)
            peso = serializer.validated_data.get('peso_porcentual', tarea_anterior.peso_porcentual)
            self._assert_pesos_total_100_para_publicar(
                asignatura=asignatura,
                exclude_tarea_id=tarea_anterior.id,
                peso_nuevo=peso,
            )

        tarea = serializer.save()

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

        # Exigir que el total de pesos sea 100% antes de publicar
        try:
            self._assert_pesos_total_100_para_publicar(asignatura=tarea.asignatura)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        
        tarea.estado = 'publicada'
        tarea.save()

        estudiantes_notificados = self._count_estudiantes_notificados(tarea)
        
        # Notificar estudiantes
        enviar_notificacion_tarea.delay(tarea.id)
        
        return Response({
            'message': 'Tarea publicada exitosamente',
            'estudiantes_notificados': estudiantes_notificados,
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


class EntregaTareaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Entregas de Tareas
    - Estudiantes: solo pueden crear/ver sus propias entregas
    - Docentes: pueden ver entregas de sus asignaturas y calificar
    - Coordinadores/Admins: pueden ver entregas de su facultad
    """
    serializer_class = EntregaTareaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tarea', 'estudiante', 'estado_entrega']
    search_fields = ['estudiante__username', 'estudiante__first_name', 'estudiante__last_name', 'tarea__titulo']
    ordering = ['-fecha_entrega']
    
    def get_queryset(self):
        """
        Filtrar entregas según el rol:
        - Estudiante: solo sus propias entregas
        - Docente: entregas de sus asignaturas
        - Coordinador/Admin: entregas de su facultad
        - Super Admin: todas las entregas
        """
        user = self.request.user
        
        # Obtener roles
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Super Admin ve todas las entregas
        if 'super_admin' in user_roles:
            return EntregaTarea.objects.select_related(
                'tarea', 'tarea__asignatura', 'estudiante'
            ).all()
        
        # Coordinador ve entregas de su facultad
        if 'coordinador' in user_roles:
            if user.facultad:
                return EntregaTarea.objects.select_related(
                    'tarea', 'tarea__asignatura', 'estudiante'
                ).filter(
                    tarea__asignatura__carreras__facultad=user.facultad
                ).distinct()
        
        # Admin ve entregas de su facultad
        if 'admin' in user_roles:
            if user.facultad:
                return EntregaTarea.objects.select_related(
                    'tarea', 'tarea__asignatura', 'estudiante'
                ).filter(
                    tarea__asignatura__carreras__facultad=user.facultad
                ).distinct()
            # Si no tiene facultad, ve todas
            return EntregaTarea.objects.select_related(
                'tarea', 'tarea__asignatura', 'estudiante'
            ).all()
        
        # Docente ve entregas de SUS asignaturas (vía ProfesorAsignatura)
        if 'profesor' in user_roles or 'docente' in user_roles:
            from applications.academico.models import ProfesorAsignatura
            asignaturas_ids = ProfesorAsignatura.objects.filter(
                profesor=user
            ).values_list('asignatura_id', flat=True)
            return EntregaTarea.objects.select_related(
                'tarea', 'tarea__asignatura', 'estudiante'
            ).filter(
                tarea__asignatura_id__in=asignaturas_ids
            ).distinct()
        
        # Estudiante solo ve SUS propias entregas
        return EntregaTarea.objects.select_related(
            'tarea', 'tarea__asignatura', 'estudiante'
        ).filter(estudiante=user)
    
    def perform_create(self, serializer):
        """
        Al crear entrega, asignar estudiante actual y notificar docente
        """
        entrega = serializer.save(estudiante=self.request.user)
        
        # Notificar al docente responsable
        notificar_docente_nueva_entrega.delay(entrega.id)
    
    @action(detail=True, methods=['post'])
    def calificar(self, request, pk=None):
        """
        Endpoint para que el docente califique una entrega
        POST /api/entregas/{id}/calificar/
        Body: { "calificacion": 85.5, "comentarios_docente": "Excelente trabajo" }
        """
        entrega = self.get_object()
        user = request.user

        # Resolver roles (compat: roles M2M + legacy + superuser)
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        if getattr(user, 'is_superuser', False) and 'super_admin' not in user_roles:
            user_roles.append('super_admin')

        # Permisos por rol + alcance
        asignatura = entrega.tarea.asignatura
        es_docente_asignado = asignatura.profesores_asignados.filter(profesor=user).exists()

        permitido = False
        if 'super_admin' in user_roles:
            permitido = True
        elif 'admin' in user_roles or 'coordinador' in user_roles:
            facultad = getattr(user, 'facultad', None)
            if facultad and asignatura.carreras.filter(facultad=facultad).exists():
                permitido = True
        elif any(r in user_roles for r in ['profesor', 'docente']):
            permitido = bool(es_docente_asignado)

        if not permitido:
            return Response({'error': 'No tienes permiso para calificar esta entrega'}, status=status.HTTP_403_FORBIDDEN)

        # Aceptar aliases HU-09 sin romper compat
        calificacion = request.data.get('calificacion', None)
        if calificacion is None:
            calificacion = request.data.get('nota', None)

        comentarios = request.data.get('comentarios_docente', None)
        if comentarios is None:
            comentarios = request.data.get('retroalimentacion_docente', '')
        
        if calificacion is None:
            return Response(
                {'error': 'Debe proporcionar una calificación'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            calificacion = float(calificacion)
            if calificacion < 0 or calificacion > 100:
                return Response(
                    {'error': 'La calificación debe estar entre 0 y 100'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': 'La calificación debe ser un número válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entrega.calificacion = calificacion
        entrega.comentarios_docente = comentarios
        entrega.estado_entrega = 'calificada'
        entrega.fecha_calificacion = timezone.now()
        entrega.save()

        # Notificar al estudiante cuando se publique su calificación (async)
        notificar_estudiante_calificacion.delay(entrega.id)
        
        return Response({
            'message': 'Entrega calificada exitosamente',
            'entrega': EntregaTareaSerializer(entrega).data
        })
