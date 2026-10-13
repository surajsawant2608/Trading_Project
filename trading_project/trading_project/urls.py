from django.contrib import admin
from django.urls import path, include
from market_data.views import market_data_page
from market_data import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', market_data_page, name='dashboard'),
    path('market/', include('market_data.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('smart-api/', include('smart_api_integration.urls')),
    
]