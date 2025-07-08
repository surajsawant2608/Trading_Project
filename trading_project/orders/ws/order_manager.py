import threading
from orders.ws.order_updater_ws import OrderUpdateSocket
from smart_api_integration.utils import UserCredentialManager

active_ws_threads = {}

def start_order_update_ws(user_id):
    # Step 1: Check if a WebSocket thread is already running for this user
    if user_id in active_ws_threads and active_ws_threads[user_id].is_alive():
        print(f"⚠️ WebSocket for user {user_id} is already running.")
        return

    # Step 2: Fetch credentials outside the thread
    data = UserCredentialManager.get_credentials_and_tokens(user_id)
    if data["status"] != "success":
        print("❌ Error fetching credentials:", data.get("message"))
        return

    creds = data["data"]

    # Step 3: Launch WebSocket inside thread
    def run_ws():
        try:
            ws = OrderUpdateSocket(
                auth_token=creds.get("jwt_token", "NO_TOKEN_FOUND"),
                api_key=creds.get("api_key", "NO_KEY_FOUND"),
                client_code=creds.get("client_code", "NO_ID_FOUND"),
                feed_token=creds.get("feed_token", "NO_TOKEN_FOUND"),
                user_id=user_id
            )
            ws.connect()
        except Exception as e:
            print("❌ WebSocket error:", e)

    thread = threading.Thread(target=run_ws, daemon=True)
    active_ws_threads[user_id] = thread
    thread.start()
    print(f"🚀 WebSocket thread started for user {user_id}")
