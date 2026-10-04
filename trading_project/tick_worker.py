import json
import redis
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from django.contrib.auth.models import User
from smart_api_integration.models import UserApiCredentials, UserApiTokens

redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


def start_worker():

    user = User.objects.get(username="suraj")
    creds = UserApiCredentials.objects.get(user=user)
    tokens = UserApiTokens.objects.get(user=user)

    ws = SmartWebSocketV2(
        tokens.jwt_token,
        creds.api_key,
        creds.client_id,
        tokens.feed_token,
    )

    def on_open(ws):
        print("SmartAPI Connected")

        ws.subscribe(
            "abc1234",
            1,
            [{"exchangeType": 1, "tokens": ["99926000"]}]
        )

    def on_data(ws, msg):

        token = str(msg.get("token"))
        ltp = msg.get("last_traded_price")

        tick = {
            "token": token,
            "ltp": ltp
        }

        # store latest tick
        redis_client.set(f"ltp:last:{token}", json.dumps(tick))

        # publish tick
        redis_client.publish("ticks", json.dumps(tick))

    ws.on_open = on_open
    ws.on_data = on_data
    ws.connect()


if __name__ == "__main__":
    start_worker()