
from django.contrib import admin
from django.urls import path,include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="API Documentación",
        default_version='v1',
        description="Documentación de la API",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="soporte@tuempresa.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url='https://app-backendapps-prod-001-c6cjd9a8f4fggma7.eastus-01.azurewebsites.net',  # ← aquí

)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', include('app_logging.urls')),
    path('models_odoo/', include('app_odoo_models.urls')),
    path('sync_odoo/', include('odoo_endpoint.urls')),
    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger<str:format>.json|.yaml', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    

]
