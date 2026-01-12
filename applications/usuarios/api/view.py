from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model

from .serializar import UsuarioSerializer, RolSerializer, PermisoSerializer
from .permissions import TienePermiso
from .validators import validar_password, validar_passwords_coinciden
from .utils import generar_token_recuperacion, validar_token_recuperacion
from applications.academico.models import Asignatura, ProfesorAsignatura
from applications.usuarios.models import Rol, Permiso, ROLE_HIERARCHY

Usuario = get_user_model()


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión CRUD de usuarios con permisos granulares
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, TienePermiso]
    
    # Definir permisos requeridos por acción
    permisos_por_accion = {
        'create': 'crear_usuario',
        'update': 'editar_usuario',
        'partial_update': 'editar_usuario',
        'destroy': 'eliminar_usuario',
        'list': 'ver_usuarios',
        'retrieve': 'ver_usuarios',
        'me': None,  # El endpoint 'me' solo requiere estar autenticado
        'registro': None,
        'login': None,
    }
    
    def get_queryset(self):
        """
        Filtrar queryset según permisos:
        - Para list: Super_admin ve todo, admin ve estudiantes/profesores, coordinador ve docentes de su facultad
        - Para acciones detalle dejamos ver todo y delegamos la restricción a update/destroy para
          responder 403 en lugar de 404.
        - Soporte para ?carrera_id=X para filtrar docentes por facultad de una carrera específica
        """
        from django.db.models import Q
        
        user = getattr(self.request, 'user', None)

        # Sin autenticación no hay queryset
        if not user or not user.is_authenticated:
            return Usuario.objects.none()

        if self.action == 'list':
            # Parámetros de query
            rol_param = self.request.query_params.get('rol')
            carrera_id_param = self.request.query_params.get('carrera_id')

            # Resolver rol/roles del actor (compat: roles M2M + rol legacy + superuser)
            try:
                actor_roles = set(user.get_roles_tipos() or [])
            except Exception:
                actor_roles = set()
            legacy_role = getattr(user, 'rol', None)
            if legacy_role:
                actor_roles.add(legacy_role)
            if getattr(user, 'is_superuser', False):
                actor_roles.add('super_admin')
            try:
                actor_principal = user.get_rol_principal()
            except Exception:
                actor_principal = legacy_role
            
            # Si viene carrera_id, retornar profesores de esa facultad
            if carrera_id_param and rol_param == 'docente':
                from applications.academico.models import Carrera
                try:
                    carrera = Carrera.objects.get(id=carrera_id_param)
                    queryset = Usuario.objects.filter(
                        rol='profesor',
                        facultad_id=carrera.facultad_id
                    ).distinct()
                    return queryset
                except Carrera.DoesNotExist:
                    return Usuario.objects.none()
            
            # Filtro base según rol del usuario actual (para otros casos)
            if actor_principal == 'super_admin':
                queryset = Usuario.objects.all()
            elif actor_principal == 'admin':
                # Admin solo ve usuarios de su facultad
                if user.facultad:
                    queryset = Usuario.objects.filter(
                        Q(facultad=user.facultad) | Q(facultad__isnull=True)
                    )
                else:
                    queryset = Usuario.objects.none()
            elif actor_principal == 'coordinador':
                # Coordinador ve usuarios de su facultad
                if user.facultad:
                    queryset = Usuario.objects.filter(
                        Q(facultad=user.facultad) | Q(facultad__isnull=True)
                    )
                else:
                    queryset = Usuario.objects.none()
            else:
                queryset = Usuario.objects.filter(id=user.id)
            
            # Si es coordinador pidiendo docentes, filtra por su facultad
            if rol_param == 'docente' and actor_principal == 'coordinador' and hasattr(user, 'facultad') and user.facultad:
                queryset = queryset.filter(
                    Q(
                        rol='profesor',
                        facultad__isnull=True
                    ) |
                    Q(
                        rol='profesor',
                        facultad=user.facultad
                    )
                ).distinct()
            elif rol_param == 'docente':
                # Si es admin o super_admin solicitando docentes, traer todos
                queryset = queryset.filter(rol='profesor')
            
            # Filtro jerárquico HU-05 (usa rol legacy). Permite ver solo usuarios de menor jerarquía,
            # pero mantiene al propio usuario visible.
            try:
                from django.db.models import Q
                actor_level = int(getattr(user, 'get_nivel_jerarquia', lambda: 0)())
                if actor_level and actor_level < int(ROLE_HIERARCHY.get('super_admin', 5)):
                    disallowed = {tipo for tipo, lvl in ROLE_HIERARCHY.items() if int(lvl) >= actor_level}
                    # El alias 'docente' no existe como rol legacy en este proyecto
                    disallowed.discard('docente')
                    queryset = queryset.exclude(Q(rol__in=list(disallowed)) & ~Q(id=user.id))
            except Exception:
                pass

            return queryset

        # En acciones detalle devolvemos todos y delegamos la restricción a update/destroy
        return Usuario.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Obtener datos del usuario autenticado actual
        GET /api/usuarios/me/
        """
        usuario = request.user
        serializer = self.get_serializer(usuario)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def registro(self, request):
        """Alias compat: POST /api/usuarios/registro/ (mismo comportamiento que /api/auth/registro/)."""
        from .serializar import RegistroSerializer

        serializer = RegistroSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            return Response(
                {
                    'success': True,
                    'message': 'Usuario registrado exitosamente',
                    'usuario': UsuarioSerializer(usuario).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                'success': False,
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Alias compat: POST /api/usuarios/login/ (mismo comportamiento que /api/auth/login/)."""
        from rest_framework_simplejwt.tokens import RefreshToken

        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'detail': 'Email y password son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'detail': 'Credenciales inválidas.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active or user.estado == 'inactivo':
            return Response(
                {'detail': 'Tu cuenta está pendiente de aprobación por un administrador. Por favor espera.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Compatibilidad: permitir acceso si tiene rol legacy aunque aún no tenga roles M2M
        roles_tipos = []
        try:
            roles_tipos = user.get_roles_tipos()
        except Exception:
            roles_tipos = []

        if len(roles_tipos) == 0 and not getattr(user, 'rol', None):
            return Response(
                {'detail': 'Tu cuenta aún no tiene roles asignados. Por favor contacta con un administrador.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'usuario': UsuarioSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='solicitar-recuperacion')
    def solicitar_recuperacion(self, request):
        """Alias compat: POST /api/usuarios/solicitar-recuperacion/"""
        email = request.data.get('email')

        if not email:
            return Response(
                {'detail': 'El email es requerido.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usuario = Usuario.objects.get(email=email)
            token = generar_token_recuperacion(usuario)
            usuario.enviar_correo_recuperacion(token)
        except Usuario.DoesNotExist:
            # Por seguridad, no revelar si el usuario existe
            pass

        return Response(
            {'detail': 'Si el correo existe, recibirás un enlace de recuperación.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='validar-token')
    def validar_token(self, request):
        """Alias compat: POST /api/usuarios/validar-token/"""
        token = request.data.get('token')

        if not token:
            return Response(
                {'error': 'Token es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reset_token, error = validar_token_recuperacion(token)
        if error:
            return Response(
                {
                    'valido': False,
                    'mensaje': error
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                'valido': True,
                'mensaje': 'Token válido'
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='resetear-password')
    def resetear_password(self, request):
        """Alias compat: POST /api/usuarios/resetear-password/"""
        token = request.data.get('token')
        password_nueva = request.data.get('password_nueva')
        password_nueva_confirm = request.data.get('password_nueva_confirm')

        if not all([token, password_nueva, password_nueva_confirm]):
            return Response(
                {'error': 'Todos los campos son obligatorios'},
                status=status.HTTP_400_BAD_REQUEST
            )

        coinciden, mensaje = validar_passwords_coinciden(password_nueva, password_nueva_confirm)
        if not coinciden:
            return Response({'error': mensaje}, status=status.HTTP_400_BAD_REQUEST)

        reset_token, error = validar_token_recuperacion(token)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        valida, mensaje = validar_password(password_nueva)
        if not valida:
            return Response({'error': mensaje}, status=status.HTTP_400_BAD_REQUEST)

        usuario = reset_token.usuario
        usuario.set_password(password_nueva)
        usuario.save()

        reset_token.usado = True
        reset_token.save()

        return Response(
            {'detail': 'Contraseña actualizada exitosamente'},
            status=status.HTTP_200_OK
        )
    
    def update(self, request, *args, **kwargs):
        """
        Permitir que el usuario estudiante edite solo nombre, apellido y correo electrónico de su propio perfil.
        """
        usuario = self.get_object()
        user_actual = request.user

        # Si está editando a otro usuario, aplicar jerarquía HU-05
        if usuario.id != user_actual.id:
            if not user_actual.puede_editar_usuario(usuario):
                return Response(
                    {'detail': 'No tienes permiso para editar este usuario.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return super().update(request, *args, **kwargs)

        # Solo permitir modificar su propio perfil
        if usuario.id != user_actual.id:
            return Response(
                {'detail': 'No tienes permiso para editar este usuario.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Eliminar campos no permitidos
        for campo in ['username', 'numero_documento', 'rol', 'roles', 'estado', 'is_active', 'is_staff', 'is_superuser', 'facultad', 'carrera', 'asignaturas_ids']:
            request.data.pop(campo, None)

        # Solo permitir modificar first_name, last_name y email
        allowed = ['first_name', 'last_name', 'email']
        data_filtrada = {k: v for k, v in request.data.items() if k in allowed}

        serializer = UsuarioSerializer(usuario, data=data_filtrada, partial=True)

        if serializer.is_valid():
            usuario_actualizado = serializer.save()
            return Response(UsuarioSerializer(usuario_actualizado).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/usuarios/{id}/

        - Si es el propio usuario: solo permite editar first_name, last_name y email.
        - Si es un admin/super_admin editando a otro: sincroniza estado<->is_active y,
          si el usuario pasa de inactivo a activo, envía correo de aprobación.
        """
        usuario = self.get_object()
        user_actual = request.user

        prev_is_active = bool(getattr(usuario, 'is_active', False))

        # Copia mutable (QueryDict suele ser inmutable)
        data = request.data.copy()

        # Auto-edición: limitar campos
        if usuario.id == user_actual.id:
            for campo in [
                'username', 'numero_documento', 'rol', 'roles', 'estado', 'is_active', 'is_staff',
                'is_superuser', 'facultad', 'carrera', 'asignaturas_ids'
            ]:
                data.pop(campo, None)
            allowed = ['first_name', 'last_name', 'email']
            data = {k: v for k, v in data.items() if k in allowed}
        else:
            # Enforce jerarquía HU-05 para edición de terceros
            if not user_actual.puede_editar_usuario(usuario):
                return Response(
                    {'detail': 'No tienes permiso para editar este usuario.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Para edición administrativa: mantener consistencia estado/is_active
            if 'estado' in data and 'is_active' not in data:
                data['is_active'] = str(data.get('estado')).lower() == 'activo'
            elif 'is_active' in data and 'estado' not in data:
                is_active_val = data.get('is_active')
                if isinstance(is_active_val, str):
                    is_active_val = is_active_val.strip().lower() in ['true', '1', 'yes', 'y', 'si', 'sí']
                data['estado'] = 'activo' if bool(is_active_val) else 'inactivo'

        serializer = self.get_serializer(usuario, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        usuario_actualizado = serializer.save()

        # Correo al activarse (inactivo -> activo)
        now_is_active = bool(getattr(usuario_actualizado, 'is_active', False))
        if (not prev_is_active) and now_is_active:
            # Determinar roles para el correo
            roles_m2m = list(usuario_actualizado.roles.values_list('tipo', flat=True))
            roles_list = roles_m2m or ([usuario_actualizado.rol] if getattr(usuario_actualizado, 'rol', None) else [])
            roles_interes = {'estudiante', 'profesor', 'coordinador', 'admin'}
            if any(r in roles_interes for r in roles_list):
                from applications.usuarios.tasks import send_approval_welcome_email
                try:
                    send_approval_welcome_email.delay(
                        user_email=usuario_actualizado.email,
                        first_name=usuario_actualizado.first_name or usuario_actualizado.username,
                        roles=roles_list,
                    )
                except Exception:
                    pass

        return Response(self.get_serializer(usuario_actualizado).data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Eliminar usuario con validación de permiso granular
        """
        usuario = self.get_object()
        user_actual = request.user

        # Enforce jerarquía HU-05: no eliminar usuarios de igual/superior jerarquía
        if not user_actual.puede_editar_usuario(usuario):
            return Response(
                {'detail': 'No tienes permiso para eliminar este usuario.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validación: no permitir auto-eliminarse
        if usuario.id == user_actual.id:
            return Response(
                {'detail': 'No puedes eliminar tu propia cuenta.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        """Hook central para updates/parches.

        - Mantiene sincronizados `estado` y `is_active`.
        - Si el usuario pasa de inactivo -> activo, envía correo de aprobación.
        """
        usuario_prev = getattr(serializer, 'instance', None)
        was_inactive = True
        if usuario_prev is not None:
            was_inactive = (not bool(getattr(usuario_prev, 'is_active', False))) or getattr(usuario_prev, 'estado', None) == 'inactivo'

        validated = getattr(serializer, 'validated_data', {}) or {}
        estado = validated.get('estado')
        is_active = validated.get('is_active')

        save_kwargs = {}
        if estado is not None and is_active is None:
            save_kwargs['is_active'] = (estado == 'activo')
        if is_active is not None and estado is None:
            save_kwargs['estado'] = 'activo' if is_active else 'inactivo'

        usuario = serializer.save(**save_kwargs)

        now_active = bool(getattr(usuario, 'is_active', False)) and getattr(usuario, 'estado', None) != 'inactivo'
        if was_inactive and now_active:
            roles = list(usuario.roles.values_list('tipo', flat=True))
            if not roles and getattr(usuario, 'rol', None):
                roles = [usuario.rol]

            roles_objetivo = {'estudiante', 'profesor', 'coordinador', 'admin'}
            if any(r in roles_objetivo for r in roles):
                from applications.usuarios.tasks import send_approval_welcome_email
                try:
                    send_approval_welcome_email.delay(
                        user_email=usuario.email,
                        first_name=usuario.first_name or usuario.username,
                        roles=roles,
                    )
                except Exception:
                    pass


class RolViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de roles y sus permisos.
    Solo super_admin puede modificar permisos.
    """
    queryset = Rol.objects.all().prefetch_related('permisos_asignados')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Todos pueden ver roles, pero solo super_admin puede modificarlos"""
        return Rol.objects.all().prefetch_related('permisos_asignados')
    
    def create(self, request, *args, **kwargs):
        """Solo super_admin puede crear roles"""
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists() or getattr(request.user, 'rol', None) == 'super_admin'):
            return Response(
                {'detail': 'Solo super administradores pueden crear roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Solo super_admin puede actualizar roles"""
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists() or getattr(request.user, 'rol', None) == 'super_admin'):
            return Response(
                {'detail': 'Solo super administradores pueden modificar roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Solo super_admin puede eliminar roles"""
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists() or getattr(request.user, 'rol', None) == 'super_admin'):
            return Response(
                {'detail': 'Solo super administradores pueden eliminar roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['put'], url_path='permisos')
    def actualizar_permisos(self, request, pk=None):
        """
        Actualizar permisos de un rol específico.
        PUT /api/roles/{id}/permisos/
        Body: { "permisos_ids": [1, 2, 3, ...] }
        """
        if not (request.user.is_superuser or request.user.roles.filter(tipo='super_admin').exists() or getattr(request.user, 'rol', None) == 'super_admin'):
            return Response(
                {'detail': 'Solo super administradores pueden modificar permisos.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rol = self.get_object()
        permisos_ids = request.data.get('permisos_ids', [])
        
        # Validar que los permisos existen
        permisos = Permiso.objects.filter(id__in=permisos_ids)
        if len(permisos) != len(permisos_ids):
            return Response(
                {'detail': 'Algunos permisos no existen.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar permisos
        rol.permisos_asignados.set(permisos)
        
        serializer = self.get_serializer(rol)
        return Response(serializer.data)


class PermisoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para permisos.
    Todos los usuarios autenticados pueden ver la lista de permisos.
    """
    queryset = Permiso.objects.filter(activo=True).order_by('modulo', 'codigo')
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Sin paginación para obtener todos los permisos

