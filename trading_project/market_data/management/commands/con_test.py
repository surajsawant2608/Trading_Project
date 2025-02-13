import json
import websocket
import threading
import asyncio
import ssl 
import logging
import logzero
from logzero import logger
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from smart_api_integration.models import UserApiTokens, UserApiCredentials


class WebSocketClient:

    WSS_URL = "wss://smartapisocket.angelone.in/smart-stream"
    HEART_BEAT_MESSAGE = "ping"
    HEART_BEAT_INTERVAL = 10 

    def __init__(self):
        self.ws = None
        self.channel_layer = get_channel_layer()

    def on_message(self, ws, message):
        """Send WebSocket data to Django Channels"""
        data = json.loads(message)
        print("Received:", data)

        # Push data to Django Channels group
        async_to_sync(self.channel_layer.group_send)(
            "market_data_group",
            {"type": "send_market_data", "message": data},
        )

    def on_error(self, ws, error):
        print("Error:", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed:", close_status_code, close_msg)

    def on_open(self, ws):
        print("WebSocket connection established!")

        payload = {
            "action": 1,  # Subscribe
            "mode": 1,    # Quote mode
            "token_list": [{"exchangeType": 1, "tokens": ["26000"]}]
        }
        ws.send(json.dumps(payload))

    def _on_pong(self, wsapp, data):
        if data == self.HEART_BEAT_MESSAGE:
            timestamp = time.time()
            formatted_timestamp = time.strftime("%d-%m-%y %H:%M:%S", time.localtime(timestamp))
            logger.info(f"In on pong function ==> {data}, Timestamp: {formatted_timestamp}")
            self.last_pong_timestamp = timestamp

    def _on_ping(self, wsapp, data):
        timestamp = time.time()
        formatted_timestamp = time.strftime("%d-%m-%y %H:%M:%S", time.localtime(timestamp))
        logger.info(f"In on ping function ==> {data}, Timestamp: {formatted_timestamp}")
        self.last_ping_timestamp = timestamp

   
    def get_user_credentials_and_tokens(self):
        """Fetch user credentials and tokens from the database"""
        try:
            user = User.objects.get(username='suraj')
            user_id = user.id

            # Fetch API credentials
            credentials = UserApiCredentials.objects.get(user_id=user_id)
            api_key = credentials.api_key
            client_id = credentials.client_id

            # Fetch API tokens
            tokens = UserApiTokens.objects.get(user_id=user_id)
            auth_token = tokens.jwt_token
            feed_token = tokens.feed_token

            return api_key, client_id, auth_token, feed_token
        except User.DoesNotExist:
            logger.error("User 'suraj' does not exist.")
        except UserApiCredentials.DoesNotExist:
            logger.error("API credentials for user 'suraj' not found.")
        except UserApiTokens.DoesNotExist:
            logger.error("API tokens for user 'suraj' not found.")
        except Exception as e:
            logger.error(f"Error fetching user credentials or tokens: {e}")

        return None, None, None, None

    def run(self):
        """Start the WebSocket connection"""
        self.api_key, self.client_id, self.auth_token, self.feed_token = self.get_user_credentials_and_tokens()

        # Ensure credentials are fetched before proceeding
        if not all([self.api_key, self.client_id, self.auth_token, self.feed_token]):
            logger.error("❌ WebSocket connection failed: Missing credentials or tokens.")
            return

        print(f"🔑 Auth Token: {self.auth_token}, Client ID: {self.client_id}")

        headers = {
            "Authorization": self.auth_token,
            "x-api-key": self.api_key,
            "x-client-code": self.client_id,
            "x-feed-token": self.feed_token
        }

        self.ws = websocket.WebSocketApp(
            self.WSS_URL,
            header=headers,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            on_ping=self._on_ping,
            on_pong=self._on_pong
        )

        try:
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, 
                                ping_interval=self.HEART_BEAT_INTERVAL, 
                                ping_payload=self.HEART_BEAT_MESSAGE)
        except Exception as e:
            logger.error(f"WebSocket run_forever encountered an error: {e}")

class Command(BaseCommand):
    help = "Start WebSocket client to fetch live market data"

    def handle(self, *args, **options):
        ws_client = WebSocketClient()
        thread = threading.Thread(target=ws_client.run, daemon=True)
        thread.start()
        print("WebSocket client started!")

        while True:
            asyncio.sleep(10)
