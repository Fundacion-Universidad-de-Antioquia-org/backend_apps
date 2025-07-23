from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json, logging
from .utils import odoo_search_read, odoo_update
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
# Vista para traer empleados y actualizar datos
# 1) Obtenemos un logger para este módulo
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
logger = logging.getLogger(__name__)  # __name__ debe coincidir con 'tu_app.views'
param_compania = openapi.Parameter(
    'compania', openapi.IN_QUERY,
    description='ID o nombre de la compañía',
    type=openapi.TYPE_STRING,
    required=False
)
param_estado = openapi.Parameter(
    'estado', openapi.IN_QUERY,
    description='Estado del empleado',
    type=openapi.TYPE_STRING,
    required=False
)
param_prestador_id = openapi.Parameter(
    'prestador_id', openapi.IN_QUERY,
    description='ID del prestador de servicio',
    type=openapi.TYPE_INTEGER,
    required=False
)
param_codigo = openapi.Parameter(
    'codigo', openapi.IN_QUERY,
    description='Código de tripulante',
    type=openapi.TYPE_STRING,
    required=True
)
param_cedula = openapi.Parameter(
    'cedula', openapi.IN_QUERY,
    description='Cédula de empleado',
    type=openapi.TYPE_STRING,
    required=False
)

@csrf_exempt  # opcional si usas solo JWT en cabecera
@swagger_auto_schema(
    method='get',
    operation_description="Devuelve la lista de empleados, filtrable por compañía y estado",
    manual_parameters=[param_compania, param_estado],
    responses={
        200: openapi.Response(
            description='Listado de empleados',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'empleados': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def empleados_list(request):
    # 1) Solo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Leer filtros de la URL
    compania = request.GET.get('compania')
    estado   = request.GET.get('estado')

    logger.debug(f"[empleados_list] Filtros recibidos – compania={compania!r}, estado={estado!r}")

    # 3) Construir domain con solo compañía y estado
    domain = []
    if compania:
        try:
            domain.append(('company_id', '=', int(compania)))
        except ValueError:
            domain.append(('company_id.name', 'ilike', compania))
    if estado:
        domain.append(('x_studio_estado_empleado', '=', estado))

    logger.debug(f"[empleados_list] Dominio final: {domain!r}")

    # 4) Llamada a Odoo
    empleados = odoo_search_read(
        model='hr.employee',
        domain=domain or None,   # None → todos si no hay filtros
        fields=[
            'id',
            'name',
            'work_email',
            'job_id',
            'work_phone',
            'identification_id',
            'x_studio_estado_empleado'
        ],
        limit=False  
    )

    logger.debug(f"[empleados_list] Odoo devolvió {len(empleados)} empleados")

    return JsonResponse({'empleados': empleados})
@swagger_auto_schema(
    method='get',
    manual_parameters=[param_compania, param_estado,param_prestador_id],
    responses={
        200: openapi.Response(
            description='Listado de prestadores',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'empleados': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    }
)
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def prestadores_list(request):
    domain = []  # ya no metemos supplier_rank ni is_company

    if request.method == 'GET':
        compania     = request.GET.get('compania')
        estado       = request.GET.get('estado')
        prestador_id = request.GET.get('prestador_id')

        if compania:
            try:
                cid = int(compania)
            except ValueError:
                return JsonResponse({"error": "compania debe ser un entero"}, status=400)
            domain.append(['x_studio_company_id', '=', cid])

        if estado:
            # <-- reemplaza 'x_estado' por el nombre REAL de tu campo
            domain.append(['x_studio_estado', '=', estado])

        if prestador_id:
            try:
                pid = int(prestador_id)
            except ValueError:
                return JsonResponse({"error": "prestador_id debe ser un entero"}, status=400)
            domain.append(['id', '=', pid])

    prestadores = odoo_search_read(
        model='x_prestadores_de_servi',
        domain=domain or None,
        fields=[
            'id', 'x_name', 'x_studio_nombre_contratista', 'x_studio_tipo_identificacin',
            'x_studio_cdigo_ciiu', 'x_studio_partner_email'
        ],
        limit=False  
    )
    return JsonResponse({'prestadores': prestadores})
@swagger_auto_schema(
    method='get',
    manual_parameters=[],
    responses={
        200: openapi.Response(
            description='Listado de empleados del programa de conducción',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'empleados': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    }
)
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def empleados_conduccion_list(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # dominio fijo para la compañía
    domain = [
        ('company_id.name', '=', 'Programa de Conducción de Vehículos de Transporte Masivo'),
    ]

    # llamamos a Odoo sin límite de 100
    empleados = odoo_search_read(
        model='hr.employee',
        domain=domain,
        fields=[
            'name',                        # cédula
            'identification_id',           # nombre
            'x_studio_codigo',             # código tripulante
            'x_studio_estado_empleado',    # estado
            'job_title',
            'x_studio_zona_proyecto_metro',# título del puesto
            'x_studio_formacion_conduccion',
            'x_studio_correo_electrnico_personal'
        ],
        # prueba primero con False; si falla, cámbialo a 0
        limit=False  
        # o bien limit=0
    )
    # 4) Loguear la cantidad total que vino de Odoo
    total = len(empleados)
    logger.debug(f"[empleados_conduccion_list] Odoo devolvió {total} empleados")

    # Mapeo de nombres de clave JSON a campos de Odoo
    field_map = {
        'cedula': 'name',
        'nombre': 'identification_id',
        'Codigo tripulante': 'x_studio_codigo',
        'estado': 'x_studio_estado_empleado',
        'job_title': 'job_title',
        'zona': 'x_studio_zona_proyecto_metro',
        'formacion_conduccion': 'x_studio_formacion_conduccion',
        'Correo personal': 'x_studio_correo_electrnico_personal'
    }

    resultados = []
    for emp in empleados:
        emp_data = {}
        for json_key, odoo_field in field_map.items():
            valor = emp.get(odoo_field)
            # Sólo añadimos la clave si valor no es None, False ni cadena vacía
            if valor not in (None, False, ''):
                emp_data[json_key] = valor
        resultados.append(emp_data)

    return JsonResponse({'empleados': resultados})
@swagger_auto_schema(
    method='get',
    manual_parameters=[param_codigo],
    responses={
        200: openapi.Response(
            description='Empleados del programa de conducción filtrados por código',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'empleados': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    }
)
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def empleado_conduccion_por_codigo(request):
    # 1) Sólo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Leer el código desde query string
    codigo = request.GET.get('codigo')
    if not codigo:
        return JsonResponse({'error': 'Falta el parámetro "codigo".'}, status=400)
    logger.debug(f"[empleado_conduccion_por_codigo] Filtro recibido – codigo={codigo!r}")

    # 3) Construir dominio: compañía fija + filtro por código
    domain = [
        ('company_id.name', '=', 'Programa de Conducción de Vehículos de Transporte Masivo'), ('x_studio_estado_empleado', '=', 'Activo'),
    ]
    # Intentamos convertir a entero, si falla lo usamos como string
    try:
        domain.append(('x_studio_codigo', '=', int(codigo)))
    except ValueError:
        domain.append(('x_studio_codigo', '=', codigo))
    logger.debug(f"[empleado_conduccion_por_codigo] Domain final: {domain!r}")

    # 4) Llamada a Odoo sin límite de 100
    empleados = odoo_search_read(
        model='hr.employee',
        domain=domain,
        fields=[
            'name',                        # cédula
            'identification_id',           # nombre
            'x_studio_codigo',             # código tripulante
            'x_studio_estado_empleado',    # estado
            'job_title',
            'x_studio_zona_proyecto_metro',# título del puesto
            'x_studio_formacion_conduccion',# título del puesto
            'x_studio_correo_electrnico_personal'
        ],
        limit=False  # o limit=0 si tu wrapper lo prefiere
    )
    total = len(empleados)
    logger.debug(f"[empleado_conduccion_por_codigo] Odoo devolvió {total} registros")

    field_map = {
        'cedula':              'name',
        'nombre':              'identification_id',
        'Codigo tripulante':   'x_studio_codigo',
        'estado':              'x_studio_estado_empleado',
        'job_title':           'job_title',
        'zona':                'x_studio_zona_proyecto_metro',
        'formacion_conduccion':'x_studio_formacion_conduccion',
        'Correo personal':     'x_studio_correo_electrnico_personal'
    }

    resultados = []
    for emp in empleados:
        emp_data = {}
        for json_key, odoo_field in field_map.items():
            valor = emp.get(odoo_field)
            # Sólo incluimos si tiene valor significativo
            if valor not in (None, False, ''):
                emp_data[json_key] = valor
        resultados.append(emp_data)

    # 6) Devolver JSON
    return JsonResponse({'empleados': resultados})


@swagger_auto_schema(
    method='get',
    manual_parameters=[param_compania, param_estado],
    responses={
        200: openapi.Response(
            description='Contratos de empleados',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'empleados': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    })
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def contratos_list(request):
    # 1) Sólo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Parámetros
    cedula    = request.GET.get('cedula')
    estado_in = request.GET.get('estado')   # “Activo” | “Retirado”
    logger.debug("Filtros recibidos → cedula=%r, estado=%r", cedula, estado_in)

    # 3) Paso 1: resolver la cédula a un ID de hr.employee
    emp_domain = [['name', '=', cedula]] if cedula else []
    emp_rec = odoo_search_read(
        model='hr.employee',
        domain=emp_domain or None,
        fields=['id']
    )
    emp_ids = [e['id'] for e in emp_rec]
    if cedula and not emp_ids:
        logger.debug("No existe empleado con cédula %r", cedula)
        return JsonResponse({'contratos': []})

    # 4) Paso 2: construir dominio para contratos
    domain = []
    # filtro por el many2one en base al ID
    domain.append(['x_studio_many2one_field_4arFu', 'in', emp_ids])
    logger.debug("Filtro por employee_id resolvido: %r", domain[-1])

    # filtro por estado (exacto “Activo”/“Retirado”)
    if estado_in:
        e = estado_in.strip().capitalize()
        if e not in ('Activo', 'Retirado'):
            return JsonResponse(
                {'error': 'Parámetro estado inválido; use "Activo" o "Retirado".'},
                status=400
            )
        domain.append(['x_studio_estado_contrato', '=', e])
        logger.debug("Filtro por estado: %r", domain[-1])

    logger.debug("Dominio completo para contratos: %r", domain)

    # 5) Elegir campos según estado
    fields_activo = [
        'x_name',
        'x_studio_tipo_contrato',
        'x_studio_fecha_inicio_contrato',
        'x_studio_fecha_fin_contrato',
        'x_studio_estado_contrato',
        'x_studio_salario_contrato',
        'x_studio_nmero_contrato',
        'x_studio_nombre_empleado',
        'x_studio_many2one_field_jcBPU',
    ]
    fields_retirado = [
        'x_name',
        'x_studio_tipo_contrato',
        'x_studio_fecha_inicio_contrato',
        'x_studio_fecha_vencimiento_contrato',
        'x_studio_estado_contrato',
        'x_studio_many2one_field_kEZoK',
        'x_studio_salario_contrato',
        'x_studio_nmero_contrato',
        'x_studio_nombre_empleado',
        'x_studio_many2one_field_jcBPU',
    ]

    if estado_in:
        fields = fields_activo if e == 'Activo' else fields_retirado
    else:
        # unión sin duplicados
        fields = list({*fields_activo, *fields_retirado})

    logger.debug("Campos solicitados: %r", fields)

    # 6) Llamada final a Odoo
    try:
        contratos = odoo_search_read(
            model='x_contratos_empleados',
            domain=domain,
            fields=fields
        )
        logger.debug("Odoo devolvió %d contratos", len(contratos))
    except Exception as exc:
        logger.exception("Error en odoo_search_read")
        return JsonResponse({'error': str(exc)}, status=500)

    return JsonResponse({'contratos': contratos})
@swagger_auto_schema(
    method='get',
    manual_parameters=[param_compania, param_estado],
    responses={200: openapi.Response('Listado de empleados')}
)
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def estados_basicos_list(request):
    estados = odoo_search_read(
        model='x_contratos_empleados',
        fields=['id', 'name', 'state', 'active']
    )
    return JsonResponse({'estados': estados})

# Vista para traer salarios

@swagger_auto_schema(
    method='get',
    manual_parameters=[],
    responses={
        200: openapi.Response(
            description='Empleados y sus hijos activos',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'empleados': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    })
@csrf_exempt
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def empleados_y_sus_hijos_activos(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 1. Consultar hijos con empleados activos
    hijos = odoo_search_read(
        model='x_hijos',
        domain=[('x_studio_estado_empleado', '=', 'Activo')],
        fields=[
            'x_studio_many2one_field_XctqN',        # Cédula (Many2One, se extrae el valor [1])
            'x_studio_nombre_empleado_1',           # Nombre empleado
            'x_name',                               # Identificación hijo
            'x_studio_nombre',
            'x_studio_fecha_de_nacimiento',
            'x_studio_gnero',
            'x_studio_edad'
        ],
        limit=False
    )

    from collections import defaultdict
    agrupado = defaultdict(lambda: {'cedula': '', 'nombre': '', 'hijos': []})

    for hijo in hijos:
        cedula_field = hijo.get('x_studio_many2one_field_XctqN')  # [ID, valor]
        cedula = cedula_field[1] if isinstance(cedula_field, list) and len(cedula_field) > 1 else ''

        nombre = hijo.get('x_studio_nombre_empleado_1')
        if not cedula:
            continue

        agrupado[cedula]['cedula'] = cedula
        agrupado[cedula]['nombre'] = nombre
        agrupado[cedula]['hijos'].append({
            'x_name': hijo.get('x_name'),
            'x_studio_nombre': hijo.get('x_studio_nombre'),
            'x_studio_fecha_de_nacimiento': hijo.get('x_studio_fecha_de_nacimiento'),
            'x_studio_gnero': hijo.get('x_studio_gnero'),
            'x_studio_edad': hijo.get('x_studio_edad'),
        })

    return JsonResponse({'empleados': list(agrupado.values())}, safe=False)

@csrf_exempt
@swagger_auto_schema(
    method='get',
    operation_description="Devuelve lista de estudios filtrable por compañía y estado",
    manual_parameters=[param_compania, param_estado],
    responses={
        200: openapi.Response(
            description='Estudios de empleados',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'estudios': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        401: openapi.Response('No autorizado'),
        405: openapi.Response('Método no permitido'),
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def estudios_list(request):
    # 1) Sólo GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Sólo GET permitido.'}, status=405)

    # 2) Leer filtros
    compania = request.GET.get('compania')
    estado   = request.GET.get('estado')
    logger.debug(f"[estudios_list] Filtros recibidos – compania={compania!r}, estado={estado!r}")

    # 3) Construir domain Odoo
    domain = []
    if compania:
        # la relación many2one a empleado se llama x_studio_many2one_field_bEe70
        # y la compañía está en hr.employee.company_id
        try:
            # filtro por ID de compañía
            domain.append(('x_studio_many2one_field_bEe70.company_id', '=', int(compania)))
        except ValueError:
            # filtro por nombre parcial de compañía
            domain.append(('x_studio_many2one_field_bEe70.company_id.name', 'ilike', compania))
    if estado:
        domain.append(('x_studio_estado', '=', estado))

    logger.debug(f"[estudios_list] Dominio final: {domain!r}")

    # 4) Llamada a Odoo
    estudios = odoo_search_read(
        model='x_historial',
        domain=domain or None,
        fields=[
            'id',
            'x_studio_many2one_field_bEe70',
            'x_name',
            'x_studio_nombre_empleado',
            'x_studio_institucin',
            'x_studio_formacin_acadmica',
            'x_studio_nivel_de_estudio',
            'x_studio_estado',
            'x_studio_semestre_nivel',
            'x_studio_ao_de_graduacin',
            'x_studio_description',
        ],
        limit=False
    )
    logger.debug(f"[estudios_list] Odoo devolvió {len(estudios)} estudios")

    return JsonResponse({'estudios': estudios}, status=200)


class RegisterView(generics.CreateAPIView):
    """
    POST /auth/register/
    {
      "username": "...",
      "email": "...",
      "password": "...",
      "password2": "..."
    }
    """
    serializer_class   = RegisterSerializer
    permission_classes = [AllowAny]


class PasswordResetRequestView(APIView):
    """
    POST /auth/password-reset/
    { "email": "usuario@ejemplo.com" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        form = PasswordResetForm({'email': email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=None,
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
            )
        return Response({'detail': 'Mensaje enviado si el email está registrado.'})


class PasswordResetConfirmView(APIView):
    """
    POST /auth/password-reset-confirm/
    {
      "uid": "...",
      "token": "...",
      "new_password": "NuevaClave123"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64       = serializer.validated_data['uid']
        token        = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            return Response({'error': 'Usuario inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Token inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Contraseña restablecida correctamente.'})