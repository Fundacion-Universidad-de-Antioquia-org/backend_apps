import xmlrpc.client
from django.conf import settings
import os
from dotenv import load_dotenv
from rest_framework.views import exception_handler
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework import status

load_dotenv()
ODOO_URL = os.getenv("HOST")
ODOO_DB =  os.getenv("DATABASE")
ODOO_USERNAME =  os.getenv("ODOO_USER")
ODOO_PASSWORD =  os.getenv("PASSWORD")


def get_odoo_connection():
    """
    Retorna los objetos necesarios para interactuar con Odoo via XML-RPC.
    """
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return uid, models


def odoo_search_read(model, domain=None, fields=None, limit=100):
    """
    Realiza una búsqueda y lectura en un modelo de Odoo.
    """
    uid, models = get_odoo_connection()
    if domain is None:
        domain = []
    if fields is None:
        fields = []
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        model, 'search_read',
        [domain], {'fields': fields, 'limit': limit}
    )


def odoo_update(model, ids, values):
    """
    Actualiza registros en un modelo de Odoo.
    """
    uid, models = get_odoo_connection()
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        model, 'write',
        [ids, values]
    )

def custom_exception_handler(exc, context):
    # 1) Si es falta de credenciales, lo devolvemos directamente y NO llamamos al exception_handler original
    if isinstance(exc, NotAuthenticated):
        return Response(
            {'detail': 'Token JWT faltante o inválido'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    # 2) Para cualquier otra excepción, lo delegamos (envuelve en try para no romper si hay otros errores)
    try:
        return exception_handler(exc, context)
    except Exception:
        return Response(
            {'detail': 'Error interno al procesar la petición.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )