from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superusuario inicial con rol super_admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username del superusuario (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@example.com',
            help='Email del superusuario (default: admin@example.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Contraseña del superusuario (default: admin123)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Verificar si el usuario ya existe
        if Usuario.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f'El usuario "{username}" ya existe en la base de datos.'
                )
            )
            return

        # Crear el superusuario
        usuario = Usuario.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            rol='super_admin'
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Superusuario "{username}" creado exitosamente!\n'
                f'  Email: {email}\n'
                f'  Rol: Super Administrador'
            )
        )
