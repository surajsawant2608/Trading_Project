# urls.py
from django.urls import path
from . import views

app_name = 'smart_api_integration'

urlpatterns = [
    path('login/', views.user_login, name='login_page'),
    path('api_details/', views.api_details, name='api_details'),
    path('check_token_and_dashboard/', views.check_token_and_dashboard, name='check_token_and_dashboard'),
    path('reconnect_and_fetch_profile/', views.reconnect_and_fetch_profile, name='reconnect_and_fetch_profile'),
    path('profile/', views.profile, name='profile'),
]