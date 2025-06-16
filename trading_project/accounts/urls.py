from django.urls import path

# Create your views here.
from . import views

urlpatterns = [
    path("register",views.register, name='register'),
    path("login", views.login, name='login')
]
