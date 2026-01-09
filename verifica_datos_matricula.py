from applications.academico.models import Asignatura, PeriodoAcademico, Carrera
from django.contrib.auth import get_user_model
User = get_user_model()

periodo = PeriodoAcademico.objects.filter(activo=True).first()
print('Periodo activo:', periodo)
if periodo:
    asignaturas = list(Asignatura.objects.filter(periodo_academico=periodo, estado=True).values('id','nombre','carreras'))
    print('Asignaturas activas:', asignaturas)
estudiantes = User.objects.filter(roles__tipo='estudiante')
print('Estudiantes:', list(estudiantes.values('id','username','carrera')))
