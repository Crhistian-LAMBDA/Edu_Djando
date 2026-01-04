from django.core.management.base import BaseCommand
from applications.usuarios.models import Permiso


class Command(BaseCommand):
    help = 'Crea permisos iniciales del sistema'

    def handle(self, *args, **kwargs):
        permisos_a_crear = [
            # Permisos Académicos
            {
                'codigo': 'crear_asignatura',
                'nombre': 'Crear Asignatura',
                'descripcion': 'Permite crear nuevas asignaturas',
                'modulo': 'academico'
            },
            {
                'codigo': 'editar_asignatura',
                'nombre': 'Editar Asignatura',
                'descripcion': 'Permite modificar asignaturas existentes',
                'modulo': 'academico'
            },
            {
                'codigo': 'eliminar_asignatura',
                'nombre': 'Eliminar Asignatura',
                'descripcion': 'Permite eliminar asignaturas',
                'modulo': 'academico'
            },
            {
                'codigo': 'ver_asignaturas',
                'nombre': 'Ver Asignaturas',
                'descripcion': 'Permite ver listado de asignaturas',
                'modulo': 'academico'
            },
            {
                'codigo': 'crear_carrera',
                'nombre': 'Crear Carrera',
                'descripcion': 'Permite crear nuevas carreras',
                'modulo': 'academico'
            },
            {
                'codigo': 'editar_carrera',
                'nombre': 'Editar Carrera',
                'descripcion': 'Permite modificar carreras existentes',
                'modulo': 'academico'
            },
            {
                'codigo': 'eliminar_carrera',
                'nombre': 'Eliminar Carrera',
                'descripcion': 'Permite eliminar carreras',
                'modulo': 'academico'
            },
            {
                'codigo': 'ver_carreras',
                'nombre': 'Ver Carreras',
                'descripcion': 'Permite ver listado de carreras',
                'modulo': 'academico'
            },
            {
                'codigo': 'crear_facultad',
                'nombre': 'Crear Facultad',
                'descripcion': 'Permite crear nuevas facultades',
                'modulo': 'academico'
            },
            {
                'codigo': 'editar_facultad',
                'nombre': 'Editar Facultad',
                'descripcion': 'Permite modificar facultades existentes',
                'modulo': 'academico'
            },
            {
                'codigo': 'eliminar_facultad',
                'nombre': 'Eliminar Facultad',
                'descripcion': 'Permite eliminar facultades',
                'modulo': 'academico'
            },
            {
                'codigo': 'ver_facultades',
                'nombre': 'Ver Facultades',
                'descripcion': 'Permite ver listado de facultades',
                'modulo': 'academico'
            },
            {
                'codigo': 'calificar_tarea',
                'nombre': 'Calificar Tarea',
                'descripcion': 'Permite calificar tareas de estudiantes',
                'modulo': 'academico'
            },
            {
                'codigo': 'ver_notas',
                'nombre': 'Ver Notas',
                'descripcion': 'Permite ver las notas de estudiantes',
                'modulo': 'academico'
            },
            {
                'codigo': 'editar_notas',
                'nombre': 'Editar Notas',
                'descripcion': 'Permite modificar notas de estudiantes',
                'modulo': 'academico'
            },
            
            # Permisos de Usuarios
            {
                'codigo': 'crear_usuario',
                'nombre': 'Crear Usuario',
                'descripcion': 'Permite crear nuevos usuarios',
                'modulo': 'usuarios'
            },
            {
                'codigo': 'editar_usuario',
                'nombre': 'Editar Usuario',
                'descripcion': 'Permite modificar usuarios existentes',
                'modulo': 'usuarios'
            },
            {
                'codigo': 'eliminar_usuario',
                'nombre': 'Eliminar Usuario',
                'descripcion': 'Permite eliminar usuarios',
                'modulo': 'usuarios'
            },
            {
                'codigo': 'ver_usuarios',
                'nombre': 'Ver Usuarios',
                'descripcion': 'Permite ver listado de usuarios',
                'modulo': 'usuarios'
            },
            {
                'codigo': 'asignar_roles',
                'nombre': 'Asignar Roles',
                'descripcion': 'Permite asignar roles a usuarios',
                'modulo': 'usuarios'
            },
            {
                'codigo': 'gestionar_permisos',
                'nombre': 'Gestionar Permisos',
                'descripcion': 'Permite gestionar permisos de roles',
                'modulo': 'usuarios'
            },
            
            # Permisos de Reportes
            {
                'codigo': 'ver_reportes_generales',
                'nombre': 'Ver Reportes Generales',
                'descripcion': 'Permite ver reportes generales del sistema',
                'modulo': 'reportes'
            },
            {
                'codigo': 'ver_reportes_academicos',
                'nombre': 'Ver Reportes Académicos',
                'descripcion': 'Permite ver reportes académicos',
                'modulo': 'reportes'
            },
            {
                'codigo': 'exportar_reportes',
                'nombre': 'Exportar Reportes',
                'descripcion': 'Permite exportar reportes a PDF/Excel',
                'modulo': 'reportes'
            },
            
            # Permisos de Notificaciones
            {
                'codigo': 'recibir_notificacion_estado_mensual',
                'nombre': 'Recibir Notificación Estado Mensual',
                'descripcion': 'Permite recibir notificaciones mensuales de estado',
                'modulo': 'notificaciones'
            },
            {
                'codigo': 'enviar_notificaciones',
                'nombre': 'Enviar Notificaciones',
                'descripcion': 'Permite enviar notificaciones a usuarios',
                'modulo': 'notificaciones'
            },
        ]

        creados = 0
        existentes = 0

        for permiso_data in permisos_a_crear:
            permiso, created = Permiso.objects.get_or_create(
                codigo=permiso_data['codigo'],
                defaults={
                    'nombre': permiso_data['nombre'],
                    'descripcion': permiso_data['descripcion'],
                    'modulo': permiso_data['modulo'],
                    'activo': True
                }
            )
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Permiso creado: {permiso_data["nombre"]}')
                )
            else:
                existentes += 1

        self.stdout.write(
            self.style.SUCCESS(f'\n=== Resumen ===')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Permisos creados: {creados}')
        )
        self.stdout.write(
            self.style.WARNING(f'Permisos ya existentes: {existentes}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total: {len(permisos_a_crear)}')
        )
