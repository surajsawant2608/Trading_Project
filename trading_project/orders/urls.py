from django.urls import path
from .views import start_order_ws

urlpatterns = [
    path("start-order-ws/", start_order_ws, name="start_order_ws"),
]
