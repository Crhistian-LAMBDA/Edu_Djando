"""
Script para crear datos iniciales de entidades académicas
"""
from applications.academico.models import Facultad, Asignatura, Carrera

# Crear Facultades
facultades_data = [
    {'nombre': 'Facultad de Ingeniería', 'codigo': 'ING', 'descripcion': 'Facultad de ciencias de la ingeniería'},
    {'nombre': 'Facultad de Ciencias', 'codigo': 'CIS', 'descripcion': 'Facultad de ciencias exactas y naturales'},
    {'nombre': 'Facultad de Humanidades', 'codigo': 'HUM', 'descripcion': 'Facultad de ciencias humanas y sociales'},
]

for fac_data in facultades_data:
    Facultad.objects.get_or_create(nombre=fac_data['nombre'], defaults=fac_data)

print('✓ Facultades creadas')

# Crear Asignaturas
asignaturas_data = [
    {'codigo': 'MAT101', 'nombre': 'Cálculo I', 'creditos': 4},
    {'codigo': 'FIS101', 'nombre': 'Física I', 'creditos': 4},
    {'codigo': 'PROG101', 'nombre': 'Programación I', 'creditos': 3},
    {'codigo': 'ALG101', 'nombre': 'Álgebra Lineal', 'creditos': 3},
    {'codigo': 'BD101', 'nombre': 'Bases de Datos', 'creditos': 4},
]

for asig_data in asignaturas_data:
    Asignatura.objects.get_or_create(codigo=asig_data['codigo'], defaults=asig_data)

print('✓ Asignaturas creadas')

# Crear Carreras
fac_ing = Facultad.objects.get(nombre='Facultad de Ingeniería')
fac_cs = Facultad.objects.get(nombre='Facultad de Ciencias')

programas_data = [
    {'codigo': 'ING-SIS', 'nombre': 'Ingeniería de Sistemas', 'facultad': fac_ing, 'nivel': 'pregrado', 'modalidad': 'presencial'},
    {'codigo': 'ING-IND', 'nombre': 'Ingeniería Industrial', 'facultad': fac_ing, 'nivel': 'pregrado', 'modalidad': 'presencial'},
    {'codigo': 'MAT', 'nombre': 'Matemáticas', 'facultad': fac_cs, 'nivel': 'pregrado', 'modalidad': 'presencial'},
    {'codigo': 'FIS', 'nombre': 'Física', 'facultad': fac_cs, 'nivel': 'pregrado', 'modalidad': 'presencial'},
]

for prog_data in programas_data:
    Carrera.objects.get_or_create(codigo=prog_data['codigo'], facultad=prog_data['facultad'], defaults=prog_data)

print('✓ Carreras creadas')
print('\n✅ Datos iniciales creados exitosamente')
