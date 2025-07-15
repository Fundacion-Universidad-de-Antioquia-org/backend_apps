
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', include('app_logging.urls')),
    path('models_odoo/', include('app_odoo_models.urls')),
    path('sync_odoo/', include('odoo_endpoint.urls')),
    

]
