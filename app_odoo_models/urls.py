from django.urls import path, include
from .views import odoo_data_endpoint

urlpatterns = [
    path('data/', odoo_data_endpoint, name='odoo_data'),
]
