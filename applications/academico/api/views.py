"""
ViewSets para modelos académicos
"""
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q
import pandas as pd
import io
from applications.academico.models import (
    Facultad,
    Asignatura,
    Carrera,
    PlanCarreraAsignatura,
    ProfesorAsignatura,
    PeriodoAcademico,
)
from applications.usuarios.tasks import send_asignatura_assignment_email, send_asignatura_desactivacion_email
from applications.usuarios.api.permissions import TienePermiso
from .serializers import (
    FacultadSerializer,
    AsignaturaSerializer,
    CarreraSerializer,
    PlanCarreraAsignaturaSerializer,
    ProfesorAsignaturaSerializer,
    PeriodoAcademicoSerializer,
)
from .permissions import (
    FacultadPermission,
    CarreraPermission,
    AsignaturaPermission,
    PlanCarreraAsignaturaPermission,
)


class FacultadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Facultades con permisos granulares"""
    queryset = Facultad.objects.all()
    serializer_class = FacultadSerializer
    permission_classes = [TienePermiso]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['nombre']
    
    permisos_por_accion = {
        'create': 'crear_facultad',
        'update': 'editar_facultad',
        'partial_update': 'editar_facultad',
        'destroy': 'eliminar_facultad',
        'list': 'ver_facultades',
        'retrieve': 'ver_facultades',
    }
    
    def get_queryset(self):
        """Filtrar facultades según rol del usuario"""
        queryset = Facultad.objects.all()
        user = self.request.user
        
        # Obtener roles del usuario
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Super Admin ve todas las facultades
        if 'super_admin' in user_roles:
            return queryset
        
        # Admin solo ve su propia facultad (solo lectura)
        if 'admin' in user_roles:
            if user.facultad:
                return queryset.filter(id=user.facultad.id)
            return Facultad.objects.none()
        
        # Coordinador solo ve su propia facultad (solo lectura)
        if 'coordinador' in user_roles:
            if user.facultad:
                return queryset.filter(id=user.facultad.id)
            return Facultad.objects.none()
        
        return queryset



class PeriodoAcademicoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Períodos Académicos"""
    queryset = PeriodoAcademico.objects.all()
    serializer_class = PeriodoAcademicoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['-fecha_inicio']

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None):
        """
        Activa este periodo académico y desactiva los demás. Solo super_admin, admin y coordinador pueden hacerlo.
        """
        user = request.user
        # Verificar roles
        roles = [r.tipo for r in getattr(user, 'roles', []).all()] if hasattr(user, 'roles') else []
        if not (user.is_superuser or 'super_admin' in roles or 'admin' in roles or 'coordinador' in roles):
            return Response({'detail': 'No tiene permisos para activar periodos.'}, status=status.HTTP_403_FORBIDDEN)

        PeriodoAcademico.objects.update(activo=False)
        periodo = self.get_object()
        periodo.activo = True
        periodo.save()
        return Response({'detail': f'Periodo {periodo.nombre} activado.'})

    @action(detail=True, methods=['post'], url_path='desactivar')
    def desactivar(self, request, pk=None):
        """
        Desactiva este periodo académico. Solo super_admin, admin y coordinador pueden hacerlo.
        """
        user = request.user
        roles = [r.tipo for r in getattr(user, 'roles', []).all()] if hasattr(user, 'roles') else []
        if not (user.is_superuser or 'super_admin' in roles or 'admin' in roles or 'coordinador' in roles):
            return Response({'detail': 'No tiene permisos para desactivar periodos.'}, status=status.HTTP_403_FORBIDDEN)

        periodo = self.get_object()
        periodo.activo = False
        periodo.save()
        return Response({'detail': f'Periodo {periodo.nombre} desactivado.'})


class AsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Asignaturas con permisos granulares"""
    serializer_class = AsignaturaSerializer
    permission_classes = [TienePermiso]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'periodo_academico', 'carreras']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['codigo']
    
    permisos_por_accion = {
        'create': 'crear_asignatura',
        'update': 'editar_asignatura',
        'partial_update': 'editar_asignatura',
        'destroy': 'eliminar_asignatura',
        'list': 'ver_asignaturas',
        'retrieve': 'ver_asignaturas',
        'importar': 'crear_asignatura',
    }
    
    def get_queryset(self):
        """
        Optimiza queries con select_related para evitar N+1 queries
        Filtra asignaturas según el rol del usuario. Para estudiantes, solo muestra asignaturas activas de su carrera.
        """
        queryset = Asignatura.objects.select_related(
            'periodo_academico'
        ).prefetch_related('carreras__facultad')

        user = self.request.user

        # Verificar roles del usuario
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]

        # Super Admin ve todas las asignaturas
        if 'super_admin' in user_roles:
            return queryset

        # Coordinador solo ve asignaturas de carreras de su facultad
        if 'coordinador' in user_roles:
            if user.facultad:
                return queryset.filter(carreras__facultad=user.facultad).distinct()
            return Asignatura.objects.none()

        # Admin ve asignaturas de su facultad
        if 'admin' in user_roles:
            if user.facultad:
                return queryset.filter(carreras__facultad=user.facultad).distinct()
            return queryset

        # Profesor/Docente solo ve SUS asignaturas (por tabla intermedia)
        if any(rol in ['profesor', 'docente'] for rol in user_roles):
            asignaturas_ids = ProfesorAsignatura.objects.filter(profesor=user).values_list('asignatura_id', flat=True)
            return queryset.filter(id__in=asignaturas_ids).distinct()

        # Estudiante: solo ve asignaturas activas de su carrera
        if 'estudiante' in user_roles:
            carrera = getattr(user, 'carrera', None)
            if carrera:
                return queryset.filter(carreras=carrera, estado=True).distinct()
            return Asignatura.objects.none()

        return queryset
    

    # Métodos de email eliminados porque la asignación de profesores ahora es solo por ProfesorAsignatura
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def importar(self, request):
        """
        Importa asignaturas desde archivo CSV/XLSX
        Parámetros:
        - archivo: archivo CSV o XLSX
        - dry_run: boolean (default True) - si es True solo valida, si es False crea las asignaturas
        - periodo_id: ID del periodo académico (opcional, usa el activo si no se especifica)
        
        Columnas esperadas del archivo:
        - Carrera: nombre exacto de la carrera
        - Semestre: número del semestre
        - Materia: nombre de la asignatura
        - Créditos: número de créditos
        - Descripción: descripción (opcional)
        - Prerrequisitos: códigos separados por coma (opcional)
        """
        archivo = request.FILES.get('archivo')
        dry_run = request.data.get('dry_run', 'true').lower() == 'true'
        periodo_id = request.data.get('periodo_id')
        
        if not archivo:
            return Response(
                {'error': 'No se proporcionó ningún archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determinar periodo académico
        if periodo_id:
            try:
                periodo = PeriodoAcademico.objects.get(id=periodo_id)
            except PeriodoAcademico.DoesNotExist:
                return Response(
                    {'error': f'Periodo académico con ID {periodo_id} no existe'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Usar el periodo activo
            periodo = PeriodoAcademico.objects.filter(activo=True).first()
            if not periodo:
                return Response(
                    {'error': 'No hay periodo académico activo. Especifique periodo_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Leer archivo
        try:
            file_ext = archivo.name.split('.')[-1].lower()
            if file_ext == 'csv':
                df = pd.read_csv(io.BytesIO(archivo.read()))
            elif file_ext in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(archivo.read()))
            else:
                return Response(
                    {'error': 'Formato de archivo no soportado. Use CSV o XLSX'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Error al leer archivo: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalizar nombres de columnas (remover tildes, espacios, convertir a minúsculas)
        import unicodedata
        def normalizar(texto):
            texto = str(texto).strip().lower()
            texto = unicodedata.normalize('NFD', texto)
            texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
            return texto.replace(' ', '_')
        
        # Crear mapeo de columnas normalizadas
        columnas_originales = list(df.columns)
        columnas_normalizadas = {normalizar(col): col for col in columnas_originales}
        
        # Validar columnas requeridas (buscar variantes)
        columnas_requeridas = {
            'carrera': ['Carrera', 'carrera', 'CARRERA'],
            'semestre': ['Semestre', 'semestre', 'SEMESTRE', 'Sem', 'sem'],
            'materia': ['Materia', 'materia', 'MATERIA', 'Nombre', 'nombre'],
            'creditos': ['Créditos', 'Creditos', 'creditos', 'CREDITOS', 'Créd'],
            'codigo': ['Código', 'Codigo', 'codigo', 'CODIGO', 'Código Materia', 'Codigo Materia']
        }
        
        # Mapeo final de columnas encontradas
        columnas_mapa = {}
        errores_columnas = []
        
        for clave, variantes in columnas_requeridas.items():
            encontrada = None
            for variante in variantes:
                if variante in df.columns:
                    encontrada = variante
                    break
            if encontrada:
                columnas_mapa[clave] = encontrada
            else:
                errores_columnas.append(clave)
        
        if errores_columnas:
            return Response(
                {'error': f'Columnas faltantes: {", ".join(errores_columnas)}. Columnas disponibles: {", ".join(df.columns)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificación adicional: asegurar que todas las claves requeridas están en el mapeo
        claves_requeridas = ['carrera', 'semestre', 'materia', 'creditos', 'codigo']
        for clave in claves_requeridas:
            if clave not in columnas_mapa:
                return Response(
                    {'error': f'Error interno: columna {clave} no mapeada correctamente'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Procesar filas
        resultados = {
            'total': len(df),
            'validas': 0,
            'invalidas': 0,
            'creadas': 0,
            'filas': []
        }
        
        # Guardar índices originales para reportes de error
        df['_fila_original'] = df.index + 2  # +2 porque Excel empieza en 1 y tiene header
        
        # Ordenar por semestre para que prerrequisitos se creen en orden correcto
        try:
            df = df.sort_values(by=columnas_mapa['semestre'], ascending=True)
        except Exception:
            pass  # Si no puede ordenar, continúa sin ordenar
        
        # Sin cache - búsqueda flexible en cada fila
        for idx, row in df.iterrows():
            # Limpiar NaN values de pandas para que sean JSON serializable
            row_dict = row.to_dict()
            row_dict_limpio = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
            
            fila_resultado = {
                'fila': int(row['_fila_original']),  # Usar fila original del Excel
                'datos': row_dict_limpio,
                'errores': [],
                'advertencias': [],
                'creada': False
            }
            
            # Inicializar variables
            carrera = None
            codigo_asignatura = None
            semestre = None
            creditos = None
            
            # Validar carrera (búsqueda flexible: case-insensitive)
            try:
                nombre_carrera = str(row[columnas_mapa['carrera']]).strip()
            except (KeyError, IndexError, TypeError):
                fila_resultado['errores'].append('Error al leer columna Carrera')
                nombre_carrera = ''
            
            if not nombre_carrera or nombre_carrera == 'nan':
                fila_resultado['errores'].append('Carrera no puede estar vacía')
            else:
                carrera = Carrera.objects.filter(nombre__iexact=nombre_carrera).first()
                if not carrera:
                    fila_resultado['errores'].append(f'Carrera "{nombre_carrera}" no existe')
            
            # Validar código (requerido y debe ser único)
            try:
                codigo_asignatura = str(row[columnas_mapa['codigo']]).strip()
            except (KeyError, IndexError):
                fila_resultado['errores'].append('Error al leer columna Código')
                codigo_asignatura = None
            
            if codigo_asignatura and codigo_asignatura != 'nan':
                if Asignatura.objects.filter(codigo=codigo_asignatura).exists():
                    fila_resultado['errores'].append(f'Código "{codigo_asignatura}" ya existe')
            else:
                fila_resultado['errores'].append('Código no puede estar vacío')
            
            # Validar semestre
            semestre = None
            try:
                val_semestre = str(row[columnas_mapa['semestre']]).strip()
                if val_semestre and val_semestre != 'nan':
                    semestre = int(float(val_semestre))
                    if semestre < 1 or semestre > 12:
                        fila_resultado['errores'].append('Semestre debe estar entre 1 y 12')
                        semestre = None
                else:
                    fila_resultado['errores'].append('Semestre no puede estar vacío')
            except (ValueError, TypeError, KeyError, IndexError) as e:
                fila_resultado['errores'].append(f'Semestre debe ser un número entero')
                semestre = None
            
            # Validar créditos
            creditos = None
            try:
                val_creditos = str(row[columnas_mapa['creditos']]).strip()
                if val_creditos and val_creditos != 'nan':
                    creditos = int(float(val_creditos))
                    if creditos < 1:
                        fila_resultado['errores'].append('Créditos debe ser mayor a 0')
                        creditos = None
                else:
                    fila_resultado['errores'].append('Créditos no puede estar vacío')
            except (ValueError, TypeError, KeyError, IndexError) as e:
                fila_resultado['errores'].append(f'Créditos debe ser un número entero')
                creditos = None
            
            # Nombre de asignatura
            nombre_materia = None
            try:
                nombre_materia = str(row[columnas_mapa['materia']]).strip()
            except (KeyError, IndexError, TypeError):
                fila_resultado['errores'].append('Error al leer columna Materia')
                nombre_materia = None
            
            if not nombre_materia or nombre_materia == 'nan':
                fila_resultado['errores'].append('Materia no puede estar vacía')
            
            # Descripción (opcional) - buscar en cualquier variante de nombre
            descripcion = ''
            for col_name in df.columns:
                if col_name.lower() in ['descripción', 'descripcion', 'descripció']:
                    descripcion = str(row[col_name]).strip()
                    break
            if descripcion == 'nan':
                descripcion = ''
            
            # Prerrequisitos (opcional) - solo advertencia, no bloquea creación
            # buscar en cualquier variante de nombre
            prerrequisitos_str = ''
            for col_name in df.columns:
                if col_name.lower() in ['prerrequisitos', 'prerrequisito', 'prerequisitos', 'prerequisito']:
                    prerrequisitos_str = str(row[col_name]).strip()
                    break
            prerrequisitos = []
            advertencias = []
            # Ignorar valores vacíos, nan, guiones (-, —, –), etc.
            if prerrequisitos_str and prerrequisitos_str not in ['nan', '', '-', '—', '–', 'N/A', 'n/a']:
                codigos_prereq = [c.strip() for c in prerrequisitos_str.split(',') if c.strip() and c.strip() not in ['-', '—', '–']]
                if codigos_prereq:  # Solo validar si hay códigos reales
                    prereq_existentes = Asignatura.objects.filter(codigo__in=codigos_prereq)
                    codigos_encontrados = set(prereq_existentes.values_list('codigo', flat=True))
                    codigos_no_encontrados = [c for c in codigos_prereq if c not in codigos_encontrados]
                    if codigos_no_encontrados:
                        # Solo advertencia, no error
                        advertencias.append(
                            f'Prerrequisitos no encontrados (se omitirán): {", ".join(codigos_no_encontrados)}'
                        )
                    prerrequisitos = list(prereq_existentes)
            
            # Agregar advertencias al resultado pero no como errores bloqueantes
            if advertencias:
                fila_resultado['advertencias'] = advertencias
            
            # El código viene del Excel, NO se genera
            # (validación de unicidad ya hecha arriba)
            
            # Si hay errores, marcar como inválida
            if fila_resultado['errores']:
                resultados['invalidas'] += 1
            else:
                # Validar que todos los datos necesarios estén presentes
                if not carrera or not semestre or not creditos or not nombre_materia or not codigo_asignatura:
                    fila_resultado['errores'].append('Faltan datos requeridos (carrera, semestre, créditos, código o nombre)')
                    resultados['invalidas'] += 1
                else:
                    resultados['validas'] += 1
                    fila_resultado['codigo_usado'] = codigo_asignatura
                    
                    # Si no es dry_run, crear la asignatura
                    if not dry_run:
                        try:
                            with transaction.atomic():
                                asignatura = Asignatura.objects.create(
                                    nombre=nombre_materia,
                                    codigo=codigo_asignatura,
                                    descripcion=descripcion,
                                    creditos=creditos,
                                    estado=True,
                                    docente_responsable=None,
                                    periodo_academico=periodo
                                )
                                
                                # Crear relación con carrera en PlanCarreraAsignatura
                                PlanCarreraAsignatura.objects.create(
                                    carrera=carrera,
                                    asignatura=asignatura,
                                    semestre=semestre,
                                    es_obligatoria=True
                                )
                                
                                # Enlazar prerrequisitos si existen
                                if prerrequisitos:
                                    asignatura.prerrequisitos.set(prerrequisitos)
                                
                                fila_resultado['creada'] = True
                                resultados['creadas'] += 1
                        except Exception as e:
                            fila_resultado['errores'].append(f'Error al crear: {str(e)}')
                            resultados['invalidas'] += 1
                            resultados['validas'] -= 1
            
            resultados['filas'].append(fila_resultado)
        
        resultados['modo'] = 'validación' if dry_run else 'creación'
        resultados['periodo'] = {
            'id': periodo.id,
            'nombre': periodo.nombre
        }
        
        return Response(resultados, status=status.HTTP_200_OK)


class ProfesorAsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar relación Profesor-Asignatura"""
    queryset = ProfesorAsignatura.objects.all()
    serializer_class = ProfesorAsignaturaSerializer
    permission_classes = [IsAuthenticated]


class CarreraViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Carreras con permisos granulares"""
    serializer_class = CarreraSerializer
    permission_classes = [TienePermiso]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['facultad', 'estado', 'nivel', 'modalidad']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['nombre']
    
    permisos_por_accion = {
        'create': 'crear_carrera',
        'update': 'editar_carrera',
        'partial_update': 'editar_carrera',
        'destroy': 'eliminar_carrera',
        'list': 'ver_carreras',
        'retrieve': 'ver_carreras',
    }
    
    def get_queryset(self):
        """Filtrar carreras según el rol del usuario"""
        queryset = Carrera.objects.select_related('facultad')
        
        user = self.request.user
        
        # Obtener roles del usuario
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Super Admin ve todas las carreras
        if 'super_admin' in user_roles:
            return queryset
        
        # Admin ve carreras de su facultad
        if 'admin' in user_roles:
            if user.facultad:
                return queryset.filter(facultad=user.facultad)
            # Si no tiene facultad asignada, ve todas
            return queryset
        
        # Coordinador solo ve carreras de su facultad
        if 'coordinador' in user_roles:
            if user.facultad:
                return queryset.filter(facultad=user.facultad)
            # Si no tiene facultad, no ver nada
            return Carrera.objects.none()
        
        return queryset
    
    def perform_create(self, serializer):
        """Validar que coordinador solo cree carreras para su facultad"""
        user = self.request.user
        facultad_id = serializer.validated_data.get('facultad').id
        
        # Obtener roles del usuario
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Coordinador solo puede crear carreras para su facultad
        if 'coordinador' in user_roles:
            if not user.facultad or user.facultad.id != facultad_id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("El coordinador solo puede crear carreras de su facultad")
        
        # Admin solo puede crear carreras para su facultad (si está asignado)
        if 'admin' in user_roles:
            if user.facultad and user.facultad.id != facultad_id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("El administrador solo puede crear carreras de su facultad")
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Validar que no cambien la facultad de la carrera"""
        user = self.request.user
        instance = self.get_object()
        facultad_id = serializer.validated_data.get('facultad', instance.facultad).id
        
        # Validar que coordinador/admin no cambien la facultad a otra
        if facultad_id != instance.facultad.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No se puede cambiar la facultad de una carrera existente")
        
        serializer.save()


class PlanCarreraAsignaturaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Planes Carrera-Asignatura
    - Super admin y admin: CRUD completo
    - Coordinador: lectura + CRUD para planes de carreras de su facultad
    - Profesor, estudiante: Solo lectura
    """
    serializer_class = PlanCarreraAsignaturaSerializer
    permission_classes = [PlanCarreraAsignaturaPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['carrera', 'asignatura', 'semestre', 'es_obligatoria']
    search_fields = ['carrera__nombre', 'asignatura__nombre', 'asignatura__codigo']
    ordering = ['carrera', 'semestre']
    
    def get_queryset(self):
        """Filtrar planes según el rol del usuario"""
        queryset = PlanCarreraAsignatura.objects.select_related('carrera', 'asignatura')
        
        user = self.request.user
        
        # Obtener roles del usuario
        user_roles = []
        if hasattr(user, 'roles') and user.roles.exists():
            user_roles = [r.tipo for r in user.roles.all()]
        elif hasattr(user, 'rol'):
            user_roles = [user.rol]
        
        # Super Admin ve todos los planes
        if 'super_admin' in user_roles:
            return queryset
        
        # Admin ve planes de carreras de su facultad
        if 'admin' in user_roles:
            if user.facultad:
                return queryset.filter(carrera__facultad=user.facultad)
            return queryset
        
        # Coordinador solo ve planes de carreras de su facultad
        if 'coordinador' in user_roles:
            if user.facultad:
                return queryset.filter(carrera__facultad=user.facultad)
            return PlanCarreraAsignatura.objects.none()
        
        return queryset
