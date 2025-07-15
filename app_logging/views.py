from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import JsonResponse
from .models import Log
from datetime import timedelta
import logging
from dateutil import parser
from rest_framework import status

logger = logging.getLogger(__name__)

# Schema definitions for Swagger
log_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'correo': openapi.Schema(type=openapi.TYPE_STRING, description='Correo del usuario'),
        'fecha': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Fecha en formato ISO 8601'),
        'tipo_evento': openapi.Schema(type=openapi.TYPE_STRING, description='Tipo de evento, p.ej. SUCCESS'),
        'observacion': openapi.Schema(type=openapi.TYPE_STRING, description='Observaciones adicionales', default=''),
        'nombre_aplicacion': openapi.Schema(type=openapi.TYPE_STRING, description='Nombre de la aplicación que genera el log'),
        'tipo': openapi.Schema(type=openapi.TYPE_STRING, description='Nivel de log, p.ej. INFO, ERROR'),
        'id_registro': openapi.Schema(type=openapi.TYPE_STRING, description='ID interno del registro relacionado'),
    },
    required=['correo', 'fecha', 'tipo_evento']
)

# Parámetro manual para GET update_log_date
param_correo = openapi.Parameter(
    'correo', openapi.IN_QUERY,
    description='Correo del usuario a consultar',
    type=openapi.TYPE_STRING,
    required=True
)

@swagger_auto_schema(
    method='post',
    request_body=log_request_schema,
    responses={
        201: openapi.Response('Log registrado correctamente'),
        400: openapi.Response('Error en los datos')
    }
)
@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def registrar_log(request):
    """Registra un nuevo log de evento."""
    data = json.loads(request.body)
    correo = data.get('correo')
    fecha_str = data.get('fecha')
    tipo_evento = data.get('tipo_evento')
    observacion = data.get('observacion')
    nombre_aplicacion = data.get('nombre_aplicacion')
    tipo = data.get('tipo')
    id_registro = data.get('id_registro')

    if not correo or not fecha_str or not tipo_evento:
        return JsonResponse({'error': 'Campos obligatorios faltantes'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fecha = parser.isoparse(fecha_str)
    except Exception as e:
        logger.error(f"Error al parsear la fecha: {e}")
        return JsonResponse({'error': 'Fecha inválida'}, status=status.HTTP_400_BAD_REQUEST)

    Log.objects.create(
        correo=correo,
        fecha=fecha,
        tipo_evento=tipo_evento,
        observacion=observacion,
        nombre_aplicacion=nombre_aplicacion,
        tipo=tipo,
        id_registro=id_registro
    )
    return JsonResponse({'message': 'Log registrado correctamente'}, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='get',
    manual_parameters=[param_correo],
    responses={200: openapi.Response('Fecha calculada'),
               400: openapi.Response('Parámetros inválidos')}
)
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_log_date(request):
    """Calcula la próxima fecha de log esperada y si requiere justificación."""
    correo = request.GET.get('correo')
    if not correo:
        return JsonResponse({'error': 'Parametro correo es obligatorio'}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()
    today = now.date()

    last_log = Log.objects.filter(correo=correo, tipo_evento='SUCCESS').order_by('-fecha').first()
    if not last_log:
        logger.debug("No logs found for the given correo, assigning today's date.")
        return JsonResponse({
            'message': 'First log entry, using today\'s date',
            'new_date': today.strftime('%Y-%m-%d'),
            'requires_justification': False
        })

    last_reported_date = last_log.fecha.date()
    logger.debug(f"Last reported date: {last_reported_date}")

    expected_next_date = last_reported_date + timedelta(days=1)
    logger.debug(f"Expected next reporting date: {expected_next_date}")

    justification_deadline = timezone.make_aware(
        timezone.datetime.combine(last_reported_date + timedelta(days=2), timezone.datetime.min.time()) + timedelta(hours=12),
        timezone.get_current_timezone()
    )

    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())

    requires_justification = now >= justification_deadline
    logger.debug(f"Justification deadline: {justification_deadline}, Requires justification: {requires_justification}")

    if expected_next_date >= today:
        logger.debug(f"Next reporting date is today or future ({expected_next_date}), assigning today's date.")
        return JsonResponse({
            'message': 'Log already exists for today',
            'new_date': today.strftime('%Y-%m-%d'),
            'requires_justification': requires_justification
        })
    else:
        logger.debug(f"Pending date to be reported: {expected_next_date}, requires justification: {requires_justification}")
        return JsonResponse({
            'message': 'Pending log date',
            'new_date': expected_next_date.strftime('%Y-%m-%d'),
            'requires_justification': requires_justification
        })
