from django.core.management.base import BaseCommand, CommandError
from applications.academico.models import Asignatura, PeriodoAcademico
from django.db import transaction

class Command(BaseCommand):
    help = 'Mueve todas las asignaturas activas de un periodo origen a un periodo destino (actualiza el campo periodo_academico)'

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

        asignaturas = Asignatura.objects.filter(periodo_academico=periodo_origen, estado=True)
        if not asignaturas.exists():
            self.stdout.write(self.style.WARNING('No hay asignaturas activas en el periodo origen.'))
            return

        count = 0
        for asignatura in asignaturas:
            asignatura.periodo_academico = periodo_destino
            asignatura.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} asignaturas movidas de {nombre_origen} a {nombre_destino}.'))