# order/ws/my_order_ws.py

from SmartApi.smartWebSocketOrderUpdate import SmartWebSocketOrderUpdate
import json
from logzero import logger
from orders.sell_order.track_positions import handle_order_update

class OrderUpdateSocket(SmartWebSocketOrderUpdate):
    def __init__(self, auth_token, api_key, client_code, feed_token, user_id):
        super().__init__(auth_token, api_key, client_code, feed_token)
        self.user_id = user_id

    def on_message(self, wsapp, message):
        handle_order_update(self.user_id, message)
        logger.info(message)

    def on_error(self, wsapp, error):
        logger.error("WebSocket error: %s", error)

    def on_close(self, wsapp, close_status_code, close_msg):
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        super().on_close(wsapp, close_status_code, close_msg)