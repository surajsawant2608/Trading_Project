# your_app_name/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import redis
from logzero import logger
from channels.layers import get_channel_layer



class MarketDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        self.room_group_name = 'market_data'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # ✅ Initialize Redis client
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    async def disconnect(self, close_code):
        # Remove the WebSocket connection when disconnected
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        tokens = data.get("tokens", [])
        if action == "subscribe":
            try:
                # Push token list to Redis
                self.redis_client.rpush("market_data_subscriptions", json.dumps(tokens))
                await self.send(json.dumps({"status": "subscription_request_sent", "tokens": tokens}))

                # Broadcast the subscription update to SmartAPI WebSocket handler
                channel_layer = get_channel_layer()
                await channel_layer.group_send(
                    "market_data",
                    {
                        "type": "handle_subscription",
                        "tokens": tokens
                    }
                )
            except Exception as e:
                logger.error(f"Error pushing subscription to Redis: {e}")
                await self.send(json.dumps({"status": "error", "message": str(e)}))

    # Receive data from the WebSocket channel layer
    async def send_market_data(self, event):
        try:
            data = event.get("data", {})  # Get data safely
            if data:
                # Convert data to JSON string before sending
                await self.send(text_data=json.dumps(data))
            else:
                print("Warning: Received empty data in send_market_data")
        except Exception as e:
            print(f"Error in send_market_data: {e}")

    # ✅ Handle subscription requests sent from UI
    async def handle_subscription(self, event):
        tokens = event.get("tokens", [])
        if tokens:
            await self.send(json.dumps({"status": "subscribed", "tokens": tokens}))
