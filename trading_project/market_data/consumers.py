import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from channels.layers import get_channel_layer
import redis
import time
from logzero import logger
import logzero
import logging
from queue import Queue
import threading
from datetime import datetime
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
import os


# SmartAPI Credentials
# API_KEY = "8uXjWEje"
# CLIENT_ID = "S1143520"
# AUTH_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlMxMTQzNTIwIiwicm9sZXMiOjAsInVzZXJ0eXBlIjoiVVNFUiIsInRva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SjFjMlZ5WDNSNWNHVWlPaUpqYkdsbGJuUWlMQ0owYjJ0bGJsOTBlWEJsSWpvaWRISmhaR1ZmWVdOalpYTnpYM1J2YTJWdUlpd2laMjFmYVdRaU9qRXhMQ0p6YjNWeVkyVWlPaUl6SWl3aVpHVjJhV05sWDJsa0lqb2lZemMzWWpSaU5qRXRZekV5T1MwellXSmhMVGxpWXpJdE5UUTBNakpoT1RBMlkyTmhJaXdpYTJsa0lqb2lkSEpoWkdWZmEyVjVYM1l5SWl3aWIyMXVaVzFoYm1GblpYSnBaQ0k2TVRFc0luQnliMlIxWTNSeklqcDdJbVJsYldGMElqcDdJbk4wWVhSMWN5STZJbUZqZEdsMlpTSjlMQ0p0WmlJNmV5SnpkR0YwZFhNaU9pSmhZM1JwZG1VaWZYMHNJbWx6Y3lJNkluUnlZV1JsWDJ4dloybHVYM05sY25acFkyVWlMQ0p6ZFdJaU9pSlRNVEUwTXpVeU1DSXNJbVY0Y0NJNk1UYzBORGM0TmpFek5Dd2libUptSWpveE56UTBOams1TlRVMExDSnBZWFFpT2pFM05EUTJPVGsxTlRRc0ltcDBhU0k2SW1ZeFpUTmtaRFF3TFRWaVlUSXROR0ZpWmkwNE5EQmpMVEJsWXpKaE5tVTFNV1ZpTlNJc0lsUnZhMlZ1SWpvaUluMC5xYVF0X2lYRW12TDJYTGdKenF0UFpqUWFGdTFTTFAyWG02TmJJWHZ6NGFGQXNZM3RhVGt0OWRwTnUteDhxMTdPU013LVdIOTBXX0JJQTNraVU0OVZyMWUxSURPMkVXXzVsVWxhRldSTXNzLWNBRUw5dWx2Q1dGbXVhS01VUkFLN0dKczNpanNQRXhOWnJpTTFzWFppS05iWGdyZTlBYTdvYXp2RzBKZ3FEZ2siLCJBUEktS0VZIjoiOHVYaldFamUiLCJpYXQiOjE3NDQ2OTk3MzQsImV4cCI6MTc0NDc4NjEzNH0.vBwoiwINInwTzxLmw3nSaddbJEDJT7eF7qxlMgP-Pd7VBzZCQUcwng1v2i1wCbbDhoifwEyd04U6Lcl3ux02EQ"
# FEED_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlMxMTQzNTIwIiwiaWF0IjoxNzQ0Njk5NzM0LCJleHAiOjE3NDQ3ODYxMzR9.Lo-WBrAjaqKKnRWv9rgkm7M8iURgZOwES20wwXD42nMat5tsNbZc5KHXazwQRHXyTmP9eHHnOi6R5xrEgI8EFg"

class MarketDataConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        """WebSocket connection handler"""
        self.room_group_name = 'market_data'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ✅ Initialize instance variables
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.ws = None  # Ensure `self.ws` exists
        self.msg_queue = Queue()

        # ✅ Start SmartAPI WebSocket in a separate thread
        threading.Thread(target=self.start_smartapi_websocket, daemon=True).start()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.ws:
            self.ws.close_connection()
        await self.channel_layer.group_discard("market_data", self.channel_name)

    async def receive(self, text_data):
        """Handle subscribe/unsubscribe actions from frontend"""
        data = json.loads(text_data)
        action = data.get("action")
        token = data.get("tokens")
        print(token)

        if action == "subscribe":
            correlation_id = "abc1234"  
            mode = 1  
            token_list = [{"exchangeType": 2, "tokens": token}]  # Proper format
            self.ws.subscribe(correlation_id, mode, token_list)

        elif action == "unsubscribe":
            correlation_id = "abc1234"
            mode = 1
            token_list = [{"exchangeType": 2, "tokens": token}]
            self.ws.unsubscribe(correlation_id, mode, token_list)

    async def send_market_data(self, event):
        """Send market data to the frontend"""
        try:
            data = event.get("data", {})
            if data:
                await self.send(text_data=json.dumps(data))
        except Exception as e:
            logger.error(f"Error in send_market_data: {e}")

    def start_smartapi_websocket(self):
        from django.contrib.auth.models import User
        from smart_api_integration.models import UserApiCredentials, UserApiTokens
        try:
            # ✅ Get the logged-in user
            user = User.objects.get(username='suraj') 

            # ⚠️ Ensure the user is authenticated (optional if using custom user system)
            # if not user or user.is_anonymous:
            #     logger.warning("Unauthenticated user tried to connect WebSocket.")
            #     return

            # ✅ Fetch API credentials and tokens
            creds = UserApiCredentials.objects.get(user=user)
            tokens = UserApiTokens.objects.get(user=user)

            api_key = creds.api_key
            client_id = creds.client_id
            auth_token = tokens.jwt_token
            feed_token = tokens.feed_token

        except Exception as e:
            logger.error(f"Error fetching API credentials: {e}")
            return

        # ✅ Initialize SmartWebSocketV2
        self.ws = SmartWebSocketV2(auth_token, api_key, client_id, feed_token)

        correlation_id = "abc1234"
        mode = 1
        tokens = ["40495","40496","40491","40492","40487","40488"]
        token_list = [{"exchangeType": 2, "tokens": tokens}]

        def process_messages():
            """Process queued messages and send to frontend"""
            while True:
                msg_data = self.msg_queue.get()
                if msg_data:
                    try:
                        async_to_sync(get_channel_layer().group_send)(
                            "market_data",
                            {"type": "send_market_data", "data": msg_data}
                        )
                    except Exception as e:
                        logger.error(f"Error sending message to WebSocket: {e}")

        def on_open(wsapp):
            """Subscribe to tokens on open"""
            self.ws.subscribe(correlation_id, mode, token_list)
            print("Tokens Subscribed Successfully...")

        def on_data(ws, msg):
            """Handle received data"""
            self.msg_queue.put(msg)

        def on_error(ws, error):
            """Handle WebSocket error"""
            logger.error(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            """Handle WebSocket close"""
            logger.warning(f"WebSocket closed: {close_status_code}, {close_msg}")

        # Assign callbacks
        self.ws.on_open = on_open
        self.ws.on_data = on_data
        self.ws.on_error = on_error
        self.ws.on_close = on_close

        # Start WebSocket connection in a separate thread
        threading.Thread(target=self.ws.connect, daemon=True).start()
        threading.Thread(target=process_messages, daemon=True).start()