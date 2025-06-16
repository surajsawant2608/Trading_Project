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
import os

# SmartAPI Credentials
API_KEY = "8uXjWEje"
CLIENT_ID = "S1143520"
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlMxMTQzNTIwIiwicm9sZXMiOjAsInVzZXJ0eXBlIjoiVVNFUiIsInRva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SjFjMlZ5WDNSNWNHVWlPaUpqYkdsbGJuUWlMQ0owYjJ0bGJsOTBlWEJsSWpvaWRISmhaR1ZmWVdOalpYTnpYM1J2YTJWdUlpd2laMjFmYVdRaU9qRXhMQ0p6YjNWeVkyVWlPaUl6SWl3aVpHVjJhV05sWDJsa0lqb2lZemMzWWpSaU5qRXRZekV5T1MwellXSmhMVGxpWXpJdE5UUTBNakpoT1RBMlkyTmhJaXdpYTJsa0lqb2lkSEpoWkdWZmEyVjVYM1l4SWl3aWIyMXVaVzFoYm1GblpYSnBaQ0k2TVRFc0luQnliMlIxWTNSeklqcDdJbVJsYldGMElqcDdJbk4wWVhSMWN5STZJbUZqZEdsMlpTSjlMQ0p0WmlJNmV5SnpkR0YwZFhNaU9pSmhZM1JwZG1VaWZYMHNJbWx6Y3lJNkluUnlZV1JsWDJ4dloybHVYM05sY25acFkyVWlMQ0p6ZFdJaU9pSlRNVEUwTXpVeU1DSXNJbVY0Y0NJNk1UYzBNREV4TlRBMk9Dd2libUptSWpveE56UXdNREk0TkRnNExDSnBZWFFpT2pFM05EQXdNamcwT0Rnc0ltcDBhU0k2SWpsak16RmxNREkxTFRreFpUTXROR1F6WVMxaE1UbGlMV1k1WVRaaVptVmpabUppTUNJc0lsUnZhMlZ1SWpvaUluMC5CSEppRDZILU9zczhQbGNKb3djbEtrcFpiZU1pMkpOLWtIQWVlWUstTmV2blZ0QmloRUdVZXNsaFlFYUdIR2ZIR0tBM2d1bk1kUEk4REZDY2RIQk9rd3NZMVl0dTVEODJHVkR3NUxTdzl4QjlmckQzN2RrMjl1TS1nNE5ZbWsyZ0lud3VaMHdxSExIMjVxRk9fNkNQTk5NY0ZkRUZwOU5mSW9ZNG5ZbDZmcDQiLCJBUEktS0VZIjoiOHVYaldFamUiLCJpYXQiOjE3NDAwMjg2NjgsImV4cCI6MTc0MDExNTA2OH0.ScHest9otcsZ5jgqiuj7kOTgzKSlVuYyF08KFV-cqXEkGPTpCXZPvZbyk54fq1KmWKopLT-1t24JvWikC7Xu5w"
FEED_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6IlMxMTQzNTIwIiwiaWF0IjoxNzQwMDI4NjY4LCJleHAiOjE3NDAxMTUwNjh9.EJq9-957NpuBUBmcyduzXZWq1Lu38S08yxLrgn7sSHIZ1ymbCCotLf_1KNtp0D1QToyh9FaFzBiFxeelJeBY7A"

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

        if action == "subscribe":
            correlation_id = "abc1234"  
            mode = 1  
            token_list = [{"exchangeType": 1, "tokens": [token]}]  # Proper format
            self.ws.subscribe(correlation_id, mode, token_list)

        elif action == "unsubscribe":
            correlation_id = "abc1234"
            mode = 1
            token_list = [{"exchangeType": 1, "tokens": [token]}]
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
        """Initialize and run SmartAPI WebSocket."""
        self.ws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_ID, FEED_TOKEN)

        correlation_id = "abc1234"
        mode = 1
        tokens = ["99926000", "26009"]
        token_list = [{"exchangeType": 1, "tokens": tokens}]

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