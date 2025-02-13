from django.urls import re_path
from .consumers import MarketDataConsumer

websocket_urlpatterns = [
    re_path(r'ws/market_data/$', MarketDataConsumer.as_asgi()),  # This should match your WebSocket connection in JS
]
