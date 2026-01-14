from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.db.models import Avg, Case, Count, F, IntegerField, Q, When
from django.utils import timezone

from applications.evaluaciones.models import EntregaTarea


APROBACION_UMBRAL = 51  # 51% a 100%


@dataclass(frozen=True)
class MonthWindow:
    start: datetime
    end: datetime


def month_window(year: int, month: int) -> MonthWindow:
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime(year, month, 1, 0, 0, 0), tz)

    if month == 12:
        end = timezone.make_aware(datetime(year + 1, 1, 1, 0, 0, 0), tz)
    else:
        end = timezone.make_aware(datetime(year, month + 1, 1, 0, 0, 0), tz)

    return MonthWindow(start=start, end=end)


def generar_reporte_mensual_data(year: int, month: int, top_n: int = 5) -> dict:
    window = month_window(year, month)

    # Usamos tareas del mes según fecha_vencimiento.
    entregas_qs = (
        EntregaTarea.objects
        .select_related('tarea', 'tarea__asignatura', 'tarea__asignatura__periodo_academico')
        .filter(tarea__fecha_vencimiento__gte=window.start, tarea__fecha_vencimiento__lt=window.end)
    )

    # Métricas por asignatura
    por_asignatura = (
        entregas_qs
        .values(
            'tarea__asignatura_id',
            'tarea__asignatura__codigo',
            'tarea__asignatura__nombre',
            'tarea__asignatura__periodo_academico__nombre',
        )
        .annotate(
            periodo=F('tarea__asignatura__periodo_academico__nombre'),
            total_estudiantes=Count('estudiante', distinct=True),
            promedio_general=Avg('calificacion', filter=Q(calificacion__isnull=False)),
            total_calificadas=Count('id', filter=Q(calificacion__isnull=False)),
            aprobadas=Count('id', filter=Q(calificacion__isnull=False, calificacion__gte=APROBACION_UMBRAL)),
            tareas_pendientes=Count('id', filter=Q(calificacion__isnull=True)),
        )
        .order_by('tarea__asignatura__codigo')
    )

    asignaturas = []
    for row in por_asignatura:
        total_cal = int(row.get('total_calificadas') or 0)
        aprobadas = int(row.get('aprobadas') or 0)
        tasa = (aprobadas / total_cal * 100.0) if total_cal else 0.0

        asignaturas.append({
            'asignatura_id': row['tarea__asignatura_id'],
            'asignatura_codigo': row['tarea__asignatura__codigo'],
            'asignatura_nombre': row['tarea__asignatura__nombre'],
            'periodo': row.get('periodo') or '',
            'total_estudiantes': int(row.get('total_estudiantes') or 0),
            'promedio_general': float(row.get('promedio_general') or 0.0),
            'tasa_aprobacion': float(tasa),
            'tareas_pendientes': int(row.get('tareas_pendientes') or 0),
        })

    # Asignaturas con mayor reprobación (top_n por % reprobación)
    reprobacion_qs = (
        por_asignatura
        .annotate(
            reprobadas=Case(
                When(total_calificadas=0, then=0),
                default=F('total_calificadas') - F('aprobadas'),
                output_field=IntegerField(),
            )
        )
    )

    reprobacion = []
    for row in reprobacion_qs:
        total = int(row.get('total_calificadas') or 0)
        reprobadas = int(row.get('reprobadas') or 0)
        fail_rate = (reprobadas / total * 100.0) if total else 0.0
        reprobacion.append({
            'asignatura_codigo': row['tarea__asignatura__codigo'],
            'asignatura_nombre': row['tarea__asignatura__nombre'],
            'reprobacion_pct': float(fail_rate),
        })

    reprobacion.sort(key=lambda x: x['reprobacion_pct'], reverse=True)

    # Docentes con mejor promedio (top_n por promedio de calificaciones)
    docentes_qs = (
        entregas_qs
        .filter(calificacion__isnull=False)
        .values(
            'tarea__asignatura__profesores_asignados__profesor_id',
            'tarea__asignatura__profesores_asignados__profesor__username',
            'tarea__asignatura__profesores_asignados__profesor__first_name',
            'tarea__asignatura__profesores_asignados__profesor__last_name',
        )
        .annotate(promedio=Avg('calificacion'))
    )

    docentes = []
    for row in docentes_qs:
        prof_id = row.get('tarea__asignatura__profesores_asignados__profesor_id')
        if not prof_id:
            continue

        nombre = (
            f"{(row.get('tarea__asignatura__profesores_asignados__profesor__first_name') or '').strip()} "
            f"{(row.get('tarea__asignatura__profesores_asignados__profesor__last_name') or '').strip()}"
        ).strip()
        if not nombre:
            nombre = (row.get('tarea__asignatura__profesores_asignados__profesor__username') or '').strip()

        docentes.append({
            'docente_id': int(prof_id),
            'docente_nombre': nombre,
            'promedio': float(row.get('promedio') or 0.0),
        })

    docentes.sort(key=lambda x: x['promedio'], reverse=True)

    data = {
        'year': year,
        'month': month,
        'fecha_generacion': timezone.now().isoformat(),
        'metricas_por_asignatura': asignaturas,
        'asignaturas_con_mayor_reprobacion': reprobacion[:top_n],
        'docentes_con_mejor_promedio': docentes[:top_n],
    }

    return data
