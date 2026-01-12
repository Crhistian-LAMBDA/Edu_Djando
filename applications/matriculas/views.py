"""ViewSets para Matrículas."""

from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Matricula
from .serializers import MatriculaSerializer
from applications.academico.models import Asignatura, PeriodoAcademico
from applications.academico.api.serializers import AsignaturaSerializer

class MatriculaViewSet(viewsets.ModelViewSet):
    serializer_class = MatriculaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]

        if getattr(user, 'is_superuser', False) and 'super_admin' not in user_roles:
            user_roles.append('super_admin')

        # Super admin ve todo
        if 'super_admin' in user_roles:
            return Matricula.objects.all()

        # Admin/Coordinador: alcance por facultad
        if 'admin' in user_roles or 'coordinador' in user_roles:
            facultad = getattr(user, 'facultad', None)
            if not facultad:
                return Matricula.objects.none()
            return Matricula.objects.filter(estudiante__carrera__facultad=facultad).distinct()

        # Estudiante: solo sus matrículas
        return Matricula.objects.filter(estudiante=user)

    def perform_create(self, serializer):
        # Validar que asignatura y periodo existan y sean válidos
        asignatura = serializer.validated_data.get('asignatura')
        periodo = serializer.validated_data.get('periodo')
        user = self.request.user
        if not asignatura or not periodo:
            raise serializers.ValidationError({'detail': 'Asignatura y periodo son obligatorios.'})
        # Validar que la asignatura esté activa y corresponda a la carrera y periodo
        carrera = getattr(user, 'carrera', None)
        if not carrera:
            raise serializers.ValidationError({'detail': 'El usuario no tiene carrera asignada.'})
        if not asignatura.estado or asignatura.periodo_academico != periodo or not asignatura.carreras.filter(id=carrera.id).exists():
            raise serializers.ValidationError({'detail': 'La asignatura no es válida para tu carrera o periodo.'})
        # Validar que no exista matrícula previa
        if Matricula.objects.filter(estudiante=user, asignatura=asignatura, periodo=periodo).exists():
            raise serializers.ValidationError({'detail': 'Ya tienes esta asignatura matriculada en este periodo.'})
        serializer.save(estudiante=user)

    @action(detail=False, methods=['get'], url_path='disponibles')
    def disponibles(self, request):
        """
        Devuelve las asignaturas activas de la carrera del estudiante que NO ha matriculado en el periodo académico activo.
        """
        user = request.user
        carrera = getattr(user, 'carrera', None)
        if not carrera:
            return Response({'detail': 'El usuario no tiene carrera asignada.'}, status=status.HTTP_400_BAD_REQUEST)

        periodo = PeriodoAcademico.objects.filter(activo=True).first()
        if not periodo:
            return Response({'detail': 'No hay periodo académico activo.'}, status=status.HTTP_400_BAD_REQUEST)

        # IDs de asignaturas ya matriculadas por el usuario en el periodo activo
        ya_matriculadas = Matricula.objects.filter(estudiante=user, periodo=periodo).values_list('asignatura_id', flat=True)

        # Asignaturas activas de la carrera, excluyendo las ya matriculadas
        disponibles = Asignatura.objects.filter(carreras=carrera, estado=True, periodo_academico=periodo).exclude(id__in=ya_matriculadas).distinct()
        data = AsignaturaSerializer(disponibles, many=True).data
        return Response(data)