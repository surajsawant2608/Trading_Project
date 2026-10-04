# """
# URL configuration for trading_project project.

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/5.1/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path,include
# from smart_api_integration import views
# from django.contrib.auth.views import LogoutView, LoginView
# # from orders.views import start_order_ws

# urlpatterns = [
#     path('',views.user_login, name='login'),
#     # path('', LoginView.as_view(template_name='login.html'), name='login'),
#     # path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
#     path('admin/', admin.site.urls),
#     path('accounts/', include('django.contrib.auth.urls')),  # Include Django's auth URLs
#     path('', include(('smart_api_integration.urls', 'smart_api_integration'), namespace='smart_api_integration')),
#     path('', include('market_data.urls')),
#     path("orders/", include("orders.urls")),
#     path('accounts/',include('accounts.urls'))
# ]


from django.contrib import admin
from django.urls import path
from django.shortcuts import render

# Direct test view to verify the template renders
def test_dashboard(request):
    return render(request, "dashboard.html")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', test_dashboard, name='dashboard'),
]