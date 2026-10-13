# urls.py
from django.urls import path, include
from django.contrib import admin
from .views import dashboard_view
from . import views

app_name = 'smart_api_integration'

urlpatterns = [
    # path('login/', views.user_login, name='login_page'),
    # path('api_details/', views.api_details, name='api_details'),
    path('check_token_and_dashboard/', views.check_token_and_dashboard, name='check_token_and_dashboard'),
    path('reconnect_and_fetch_profile/', views.reconnect_and_fetch_profile, name='reconnect_and_fetch_profile'),
    path('profile/', views.profile, name='profile'),
    path('admin/', admin.site.urls),
    
    # Route the root URL directly to your dashboard
    path('', dashboard_view, name='dashboard'), 
    
    # Keep the auth urls if you still want to log in later
    path('accounts/', include('django.contrib.auth.urls')),
    ]