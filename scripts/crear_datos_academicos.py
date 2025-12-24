"""
Script para crear datos iniciales de entidades académicas
"""
from applications.usuarios.models import Facultad, Asignatura, Programa

# Crear Facultades
facultades_data = [
    {'nombre': 'Facultad de Ingeniería', 'descripcion': 'Facultad de ciencias de la ingeniería'},
    {'nombre': 'Facultad de Ciencias', 'descripcion': 'Facultad de ciencias exactas y naturales'},
    {'nombre': 'Facultad de Humanidades', 'descripcion': 'Facultad de ciencias humanas y sociales'},
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

# Crear Programas
fac_ing = Facultad.objects.get(nombre='Facultad de Ingeniería')
fac_cs = Facultad.objects.get(nombre='Facultad de Ciencias')

programas_data = [
    {'codigo': 'ING-SIS', 'nombre': 'Ingeniería de Sistemas', 'facultad': fac_ing},
    {'codigo': 'ING-IND', 'nombre': 'Ingeniería Industrial', 'facultad': fac_ing},
    {'codigo': 'MAT', 'nombre': 'Matemáticas', 'facultad': fac_cs},
    {'codigo': 'FIS', 'nombre': 'Física', 'facultad': fac_cs},
]

for prog_data in programas_data:
    Programa.objects.get_or_create(codigo=prog_data['codigo'], defaults=prog_data)

print('✓ Programas creados')
print('\n✅ Datos iniciales creados exitosamente')
