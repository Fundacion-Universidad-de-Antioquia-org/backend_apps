from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .utils import (
    fetch_x_bancos,
    fetch_x_eps,
    fetch_x_arl,
    fetch_x_afp,
    fetch_x_banco,
    fetch_x_centro_costos,
    fetch_x_talla_camisa,
    fetch_x_talla_calzado,
    fetch_x_talla_pantalon,
    fetch_x_paises,
    fetch_x_cesantias,
    fetch_x_poblaciones_vul,
    fetch_x_hobbies_options,
    fetch_x_actividad_economica

)
@swagger_auto_schema(
    method='get',
    responses={200: openapi.Response(
        description='Diccionario con todos los datos Odoo',
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'paises': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'municipios': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'eps': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'arl': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'banco': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'centro_costos': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'talla_camisa': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'talla_calzado': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'talla_pantalon': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'cesantias': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'poblaciones_vul': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'hobbies_options': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                'actividad_economica': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                # … repite para cada clave …
            }
        )
    )}
)
@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def odoo_data_endpoint(request):
    """
    Endpoint que junta la información de los distintos modelos en Odoo:
    - Municipios (x_bancos)
    - EPS (x_eps)
    - ARL (x_arl)
    - AFP (x_afp)
    - Banco (x_banco)
    - Centro Costos (x_centro_costos)
    - Talla Camisa (x_talla_camisa)
    - Talla Calzado (x_talla_calzado)
    - Talla Pantalón (x_talla_pantalon)
    """
    response_data = {
        "paises":fetch_x_paises(),
        "municipios": fetch_x_bancos(),
        "eps": fetch_x_eps(),
        "arl": fetch_x_arl(),
        "afp": fetch_x_afp(),
        "banco": fetch_x_banco(),
        "centro_costos": fetch_x_centro_costos(),
        "talla_camisa": fetch_x_talla_camisa(),
        "talla_calzado": fetch_x_talla_calzado(),
        "talla_pantalon": fetch_x_talla_pantalon(),
        "cesantias":fetch_x_cesantias(),
        "poblaciones_vul": fetch_x_poblaciones_vul(),
        "hobbies_options": fetch_x_hobbies_options(),
        "actividad_economica": fetch_x_actividad_economica(),
    }
    return JsonResponse(response_data)
