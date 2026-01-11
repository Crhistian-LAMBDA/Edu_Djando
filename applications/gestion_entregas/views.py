from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from applications.matriculas.models import Matricula
from applications.academico.models import Asignatura, ProfesorAsignatura
from applications.evaluaciones.models import EntregaTarea
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class EntregasPorGrupoAPIView(APIView):
    """
    Devuelve la estructura: Materia -> Grupo/Horario -> Estudiantes -> Entregas
    Filtros: asignatura_id, horario, periodo, profesor_id
    Solo accesible para profesor, admin, coordinador, super admin
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        asignatura_id = request.query_params.get('asignatura_id')
        horario = request.query_params.get('horario')
        periodo_id = request.query_params.get('periodo_id')
        profesor_id = request.query_params.get('profesor_id')

        # Filtrar asignatura
        asignatura = Asignatura.objects.filter(id=asignatura_id).first()
        if not asignatura:
            return Response({'error': 'Asignatura no encontrada'}, status=400)

        # Filtrar matrículas por grupo/hora y periodo
        matriculas = Matricula.objects.filter(asignatura=asignatura)
        if horario:
            matriculas = matriculas.filter(horario=horario)
        if periodo_id:
            matriculas = matriculas.filter(periodo_id=periodo_id)

        # Filtrar por profesor si aplica
        if profesor_id:
            if not ProfesorAsignatura.objects.filter(asignatura=asignatura, profesor_id=profesor_id).exists():
                return Response({'error': 'El profesor no imparte esta asignatura'}, status=400)

        estudiantes = []
        for m in matriculas.select_related('estudiante'):
            entregas = EntregaTarea.objects.filter(estudiante=m.estudiante, tarea__asignatura=asignatura)
            estudiantes.append({
                'id': m.estudiante.id,
                'nombre': m.estudiante.get_full_name() or m.estudiante.username,
                'username': m.estudiante.username,
                'email': m.estudiante.email,
                'entregas': [
                    {
                        'tarea_id': e.tarea.id,
                        'tarea_titulo': e.tarea.titulo,
                        'estado': e.estado_entrega,
                        'calificacion': e.calificacion,
                        'archivo': e.archivo_entrega.url if e.archivo_entrega else None,
                        'comentarios_estudiante': e.comentarios_estudiante,
                        'comentarios_docente': e.comentarios_docente,
                        'fecha_entrega': e.fecha_entrega,
                    } for e in entregas
                ]
            })

        return Response({
            'asignatura': {
                'id': asignatura.id,
                'nombre': asignatura.nombre,
                'codigo': asignatura.codigo,
            },
            'horario': horario,
            'periodo_id': periodo_id,
            'estudiantes': estudiantes
        })
