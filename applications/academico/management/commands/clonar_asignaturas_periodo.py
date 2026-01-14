from django.core.management.base import BaseCommand, CommandError
from applications.academico.models import Asignatura, PeriodoAcademico, PlanCarreraAsignatura
from django.db import transaction

class Command(BaseCommand):
    help = 'Clona todas las asignaturas y relaciones de un periodo académico origen a uno destino.'

    def add_arguments(self, parser):
        parser.add_argument('origen', type=str, help='Nombre del periodo académico origen (ej: 2025-I)')
        parser.add_argument('destino', type=str, help='Nombre del periodo académico destino (ej: 2026-I)')

    @transaction.atomic
    def handle(self, *args, **options):
        nombre_origen = options['origen']
        nombre_destino = options['destino']
        try:
            periodo_origen = PeriodoAcademico.objects.get(nombre=nombre_origen)
            periodo_destino = PeriodoAcademico.objects.get(nombre=nombre_destino)
        except PeriodoAcademico.DoesNotExist:
            raise CommandError('Uno de los periodos no existe.')

        asignaturas_origen = Asignatura.objects.filter(periodo_academico=periodo_origen)
        if not asignaturas_origen.exists():
            self.stdout.write(self.style.WARNING('No hay asignaturas en el periodo origen.'))
            return

        # Clonar asignaturas y relaciones
        for asignatura in asignaturas_origen:
            # Buscar si ya existe una asignatura con el mismo código y periodo destino
            nueva, created = Asignatura.objects.get_or_create(
                codigo=asignatura.codigo,
                periodo_academico=periodo_destino,
                defaults={
                    'nombre': asignatura.nombre,
                    'descripcion': asignatura.descripcion,
                    'creditos': asignatura.creditos,
                    'estado': asignatura.estado,
                }
            )
            # Clonar relaciones con carreras (PlanCarreraAsignatura)
            planes = PlanCarreraAsignatura.objects.filter(asignatura=asignatura)
            for plan in planes:
                PlanCarreraAsignatura.objects.get_or_create(
                    carrera=plan.carrera,
                    asignatura=nueva,
                    defaults={
                        'semestre': plan.semestre,
                        'es_obligatoria': plan.es_obligatoria,
                        'creditos_override': plan.creditos_override,
                    }
                )
        self.stdout.write(self.style.SUCCESS('Asignaturas y relaciones clonadas correctamente de %s a %s.' % (nombre_origen, nombre_destino)))
