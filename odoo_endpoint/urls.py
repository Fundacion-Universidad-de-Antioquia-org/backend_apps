from django.urls import path,re_path
from . import views
from .views import (
    RegisterView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    #ENPOINT DE AUTHENTICACIÓN
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    #ENDPOINT para ODOO
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('prestadores/', views.prestadores_list, name='prestadores_list'),
    path("empleados/conduccion/",views.empleados_conduccion_list,name="empleados_conduccion_list"),
    path("empleados/conduccion_codigo/",views.empleado_conduccion_por_codigo,name="empleado_conduccion_por_codigo"),
    path('contratos_list/', views.contratos_list, name='contratos_list'),
    path('hijos_employee/', views.empleados_y_sus_hijos_activos, name='empleados_y_sus_hijos_activos'),
    path('estudios/', views.estudios_list, name='estudios_list'),
]
