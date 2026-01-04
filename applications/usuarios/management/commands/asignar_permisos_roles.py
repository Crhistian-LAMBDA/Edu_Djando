from django.core.management.base import BaseCommand
from applications.usuarios.models import Rol, Permiso


class Command(BaseCommand):
    help = 'Asigna permisos a roles según su nivel de acceso'

    def handle(self, *args, **kwargs):
        # Obtener todos los permisos
        todos_permisos = list(Permiso.objects.all())
        
        # Super Admin: Todos los permisos
        super_admin, _ = Rol.objects.get_or_create(tipo='super_admin')
        super_admin.permisos_asignados.set(todos_permisos)
        self.stdout.write(self.style.SUCCESS(f'✓ Super Admin: {len(todos_permisos)} permisos'))
        
        # Admin (Decano): Gestión completa de usuarios y académico
        admin, _ = Rol.objects.get_or_create(tipo='admin')
        permisos_admin = Permiso.objects.filter(
            codigo__in=[
                # Usuarios
                'crear_usuario', 'editar_usuario', 'eliminar_usuario', 'ver_usuarios',
                'asignar_roles',
                # Académico
                'crear_asignatura', 'editar_asignatura', 'eliminar_asignatura', 'ver_asignaturas',
                'crear_carrera', 'editar_carrera', 'eliminar_carrera', 'ver_carreras',
                'crear_facultad', 'editar_facultad', 'eliminar_facultad', 'ver_facultades',
                'ver_notas', 'editar_notas',
                # Reportes
                'ver_reportes_generales', 'ver_reportes_academicos', 'exportar_reportes',
                # Notificaciones
                'enviar_notificaciones',
            ]
        )
        admin.permisos_asignados.set(permisos_admin)
        self.stdout.write(self.style.SUCCESS(f'✓ Admin (Decano): {permisos_admin.count()} permisos'))
        
        # Coordinador: Gestión académica de su facultad
        coordinador, _ = Rol.objects.get_or_create(tipo='coordinador')
        permisos_coordinador = Permiso.objects.filter(
            codigo__in=[
                'crear_asignatura', 'editar_asignatura', 'eliminar_asignatura', 'ver_asignaturas',
                'crear_carrera', 'editar_carrera', 'eliminar_carrera', 'ver_carreras',
                'ver_facultades',
                'ver_notas', 'editar_notas',
                'calificar_tarea',
                'ver_usuarios',
                'ver_reportes_academicos',
            ]
        )
        coordinador.permisos_asignados.set(permisos_coordinador)
        self.stdout.write(self.style.SUCCESS(f'✓ Coordinador: {permisos_coordinador.count()} permisos'))
        
        # Profesor: Ver información y calificar
        profesor, _ = Rol.objects.get_or_create(tipo='profesor')
        permisos_profesor = Permiso.objects.filter(
            codigo__in=[
                'ver_asignaturas', 'ver_carreras', 'ver_facultades',
                'calificar_tarea', 'ver_notas', 'editar_notas',
                'ver_usuarios',
            ]
        )
        profesor.permisos_asignados.set(permisos_profesor)
        self.stdout.write(self.style.SUCCESS(f'✓ Profesor: {permisos_profesor.count()} permisos'))
        
        # Estudiante: Solo lectura
        estudiante, _ = Rol.objects.get_or_create(tipo='estudiante')
        permisos_estudiante = Permiso.objects.filter(
            codigo__in=[
                'ver_asignaturas', 'ver_carreras', 'ver_facultades',
                'ver_notas',
                'recibir_notificacion_estado_mensual',  # Estudiantes reciben notificaciones
            ]
        )
        estudiante.permisos_asignados.set(permisos_estudiante)
        self.stdout.write(self.style.SUCCESS(f'✓ Estudiante: {permisos_estudiante.count()} permisos'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Permisos asignados exitosamente a todos los roles ==='))
