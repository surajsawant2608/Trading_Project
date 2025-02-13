from django.core.management.base import BaseCommand
import time
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from smart_api_integration.models import UserApiTokens, UserApiCredentials
from django.contrib.auth.models import User
from logzero import logger
from queue import Queue
import threading
from datetime import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json


class Command(BaseCommand):
    help = 'Connect to the SmartAPI WebSocket and subscribe to market data'

    def handle(self, *args, **kwargs):

        msg_queue = Queue()

        # self.ws = None
        # self.token_list = []
        # self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

        # Event for synchronization
        msg_event = threading.Event()
        
        # Fetch API credentials and tokens
        def get_user_credentials_and_tokens():
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
            except Exception as e:
                logger.error(f"Error fetching user credentials or tokens: {e}")
                return None, None, None, None

        api_key, client_id, auth_token, feed_token = get_user_credentials_and_tokens()

        if not all([api_key, client_id, auth_token, feed_token]):
            logger.error("Missing API credentials or tokens for the current user. Exiting.")
            return

        correlation_id = "check_process"
        action = 1
        mode = 1
        # token = ['26009','99926000','99926037','99926011','99926074','99926008','99926008','99926023','99926020','99926025','99926021','25','15083','508869','236','5900','16669','16675','317','383','10604','526','547','694','20374','881','910','1232','7229','1333','467','1348','500440','1394','4963','5258','1594','1660','11723','1922','11483','2031','10999','17963','11630','2475','14977','2885','21808','3045','4306','3351','3432','3456','3499','11536','13538','3506','1964','11532','3787']
        token = ['99926000','26009']
        token_list = [{"exchangeType": 1, "tokens": token}]

        def on_data(wsapp, msg):
            msg_queue.put(msg)
            
        def on_error(wsapp, error):
            print(f"WebSocket Error: {error}")

        def on_close(wsapp):
            print('Connection closed')

        def on_open(wsapp):
            print("WebSocket opened, subscribing to market data...")
            ws.subscribe(correlation_id, mode, token_list)

        # Initialize and start WebSocket connection
        ws = SmartWebSocketV2(auth_token, api_key, client_id, feed_token)
        ws.on_open = on_open
        ws.on_data = on_data
        
        # Run WebSocket in a separate thread to avoid blocking the main thread
        thread = threading.Thread(target=ws.connect, name='websocket')
        thread.start()

        # Function to process messages from the queue
        def process_messages():
            channel_layer = get_channel_layer()
            while True:
                msg_data = msg_queue.get()  # Get message from queue (blocks if empty)
                if msg_data:
                    try:
                        async_to_sync(channel_layer.group_send)(
                            "market_data",
                            {
                                "type": "send_market_data",
                                "data": msg_data
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error sending message to WebSocket: {e}")

        
        async def handle_subscription(event):
            token_channel_layer = get_channel_layer()
            tokens = event.get("tokens", [])
            if tokens:
                print(f"📩 Received new subscription request: {tokens}")

                # ✅ Send event to the 'market_data' group
                async_to_sync(token_channel_layer.group_send)(
                    "market_data",  # Group name where WebSocket consumers are listening
                    {
                        "type": "handle_subscription",
                        "tokens": tokens
                    }
                )

        # Start message processing thread
        processing_thread = threading.Thread(target=process_messages, name='message_processor')
        processing_thread.daemon = True
        processing_thread.start()

        #keep main thread alive 
        thread.join()
