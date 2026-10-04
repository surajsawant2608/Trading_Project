
import json
import threading
import queue
from collections import defaultdict
from orders.models import OpenPosition
# from orders.sell_order.track_positions import async_add_open_position
from orders.sell_order.risk_manager import RiskManager
from orders.sell_order.ltp_listener import ltp_listener

# Shared data and thread-safe lock
open_positions = defaultdict(dict)
position_lock = threading.Lock()
token_risk_managers = {}
ltp_listener_started = False

def handle_order_update(user_id,message):

    global ltp_listener_started

    """
    Process order update in background. Safely ignore heartbeat/non-JSON messages.
    """
    try:
        if isinstance(message, bytes):
            # print("[ℹ️] Skipping binary heartbeat message")
            return

        data = json.loads(message)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[ℹ️] Skipping non-JSON or malformed message: {e}")
        return

    if data.get("order-status") != "AB05":
        return

    order_data = data.get("orderData", {})
    if order_data.get("transactiontype") != "BUY":
        return

    symbol = order_data.get("tradingsymbol")
    token = order_data.get("symboltoken")
    quantity = int(order_data.get("quantity")) // 75
    avg_price = float(order_data.get("averageprice"))
    target = avg_price + ((5/100) * avg_price)
    sl = avg_price - ((3/100) * avg_price)
    order_stack = [sl,avg_price,target]
    print(f"[🟢 New Position] {symbol} {token} | Stack: {order_stack} | Qty: {quantity}")

    def on_exit_callback(reason, price):
        print(f"[🧹 Removed] {token} → {reason.upper()} at ₹{price}")
        token_risk_managers.pop(token, None)

    manager = RiskManager(
        token=token,
        symbol=symbol,
        stack=order_stack,
        total_qty=quantity,
        user_id=user_id,
        on_exit_callback=on_exit_callback
    )
    token_risk_managers[token] = manager

    # ✅ Start LTP listener in background if not already running
    if not ltp_listener_started:
        threading.Thread(target=ltp_listener, args=(token_risk_managers,), daemon=True).start()
        ltp_listener_started = True
        print("🚀 LTP Listener started")

# async_add_open_position(user_id, message)
#     orderid = order_data.get("orderid")
#     symbol = order_data.get("tradingsymbol")
#     token = order_data.get("symboltoken")
#     qty = int(order_data.get("quantity", "0"))

#     with position_lock:
#         open_positions[orderid][symbol] = {
#             "symboltoken": token,
#             "quantity": qty,
#             "avg_price": float(order_data.get("averageprice")),
#             "orderid": order_data.get("orderid"),
#         }

#         print(f"[✅ TRACKED] {orderid=} {symbol=} {qty=} @ {open_positions[orderid][symbol]['avg_price']}")


# def async_add_open_position(user_id, full_message):
#     """
#     Offload database save to a thread to avoid blocking main WebSocket message thread.
#     """
#     def save_task():
#         try:
#             # Parse the string into a dict only if it's a string
#             parsed_message = json.loads(full_message) if isinstance(full_message, str) else full_message

#             order_data = parsed_message.get("orderData", {})
#             obj, created = OpenPosition.objects.update_or_create(
#                 user_id=user_id,
#                 order_id=order_data.get('orderid', ''),
#                 defaults={
#                     "status_code": parsed_message.get("status-code", ""),
#                     "order_status": parsed_message.get("order-status", ""),
#                     "error_message": parsed_message.get("error-message", ""),
#                     **{field: order_data.get(field, "") for field in [
#                         'variety', 'ordertype', 'ordertag', 'producttype', 'price', 'triggerprice',
#                         'quantity', 'disclosedquantity', 'duration', 'squareoff', 'stoploss',
#                         'trailingstoploss', 'tradingsymbol', 'transactiontype', 'exchange',
#                         'symboltoken', 'instrumenttype', 'strikeprice', 'optiontype', 'expirydate',
#                         'lotsize', 'cancelsize', 'averageprice', 'filledshares', 'unfilledshares',
#                         'status', 'orderstatus', 'text', 'updatetime', 'exchtime', 'exchorderupdatetime',
#                         'fillid', 'filltime', 'parentorderid'
#                     ]}
#                 }
#             )
#             print(f"[{'🆕' if created else '🔁'} ASYNC SAVED] Order ID: {obj.order_id}, Status: {obj.order_status}")
#         except Exception as e:
#             print(f"[❌ ASYNC DB ERROR] {e}")

#     threading.Thread(target=save_task, daemon=True).start()
