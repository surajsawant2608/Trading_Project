import http.client
import json
from smart_api_integration.utils import UserCredentialManager

def place_order(user_id, symbol, token, quantity, transactiontype="SELL", order_type="MARKET"):
    """
    Places an order using Angel One SmartAPI.
    """
    try:
        # Step 2: Fetch credentials outside the thread

        data = UserCredentialManager.get_credentials_and_tokens(user_id)
        if data["status"] != "success":
            print("❌ Error fetching credentials:", data.get("message"))
            return

        creds = data["data"]
        api_key=creds.get("api_key")
        client_code=creds.get("client_code")
        auth_token=creds.get("jwt_token")
        user_id=user_id

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": api_key,
            "X-ClientCode": client_code,
            "Authorization": auth_token,
        }

        payload = json.dumps({
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": transactiontype,
            "exchange": "NFO",
            "ordertype": order_type,
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": str(int(quantity) * 75),  # 🧠 Lot size multiplication (make dynamic if needed)
        })

        print('📤 Placing Order Payload:', payload)

        conn = http.client.HTTPSConnection("apiconnect.angelone.in")
        conn.request("POST", "/rest/secure/angelbroking/order/v1/placeOrder", payload, headers)
        res = conn.getresponse()
        response_data = res.read().decode("utf-8")

        print('✅ Order Response:', response_data)
        return json.loads(response_data)

    except Exception as e:
        raise Exception(f"Order placement failed: {str(e)}")
