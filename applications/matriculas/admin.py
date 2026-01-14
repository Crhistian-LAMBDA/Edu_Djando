from django.contrib import admin
from .models import Matricula

@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('id', 'estudiante', 'asignatura', 'periodo', 'fecha', 'estado')
    search_fields = ('estudiante__username', 'asignatura__nombre', 'periodo__nombre')
    list_filter = ('periodo', 'estado')
    autocomplete_fields = ['estudiante', 'asignatura', 'periodo']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'asignatura':
            estudiante_id = request.GET.get('estudiante')
            from applications.academico.models import Asignatura
            if estudiante_id:
                try:
                    from applications.usuarios.models import Usuario
                    estudiante = Usuario.objects.get(pk=estudiante_id)
                    carrera = getattr(estudiante, 'carrera', None)
                    if carrera:
                        # Solo asignaturas activas de la carrera (ManyToMany a través de PlanCarreraAsignatura)
                        kwargs["queryset"] = Asignatura.objects.filter(carreras=carrera, estado=True).distinct()
                    else:
                        kwargs["queryset"] = Asignatura.objects.none()
                except Exception:
                    kwargs["queryset"] = Asignatura.objects.none()
            else:
                # Si no hay estudiante seleccionado, no mostrar ninguna asignatura
                kwargs["queryset"] = Asignatura.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
