# asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from market_data.routing import websocket_urlpatterns
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_project.settings')
django.setup()

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            # WebSocket connection URL
            websocket_urlpatterns
        )
    ),
})
