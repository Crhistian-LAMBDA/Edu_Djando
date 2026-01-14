from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.usuarios.api.permissions import TienePermiso

from applications.reportes.tasks import generar_y_enviar_reporte_mensual


class ForzarReporteMensualView(APIView):
    permission_classes = [IsAuthenticated, TienePermiso]
    permiso_requerido = 'ver_reportes_academicos'

    def post(self, request):
        hoy = timezone.localdate()
        year = int(hoy.year)
        month = int(hoy.month)

        force_resend = str(request.query_params.get('reenviar', '')).lower() in {'1', 'true', 'yes', 'si'}

        generar_y_enviar_reporte_mensual.delay(year=year, month=month, force_resend=force_resend)

        return Response(
            {
                'ok': True,
                'message': 'Reporte mensual encolado para generación/envío',
                'year': year,
                'month': month,
                'reenviar': force_resend,
            },
            status=202,
        )
