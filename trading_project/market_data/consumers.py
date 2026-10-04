import json
import redis
import threading
import re
from queue import Queue
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from logzero import logger


# ============================================================
# LOAD SCRIP MASTER
# ============================================================
SCRIP_MASTER = {}

try:
    with open(
        "/home/suraj/Suraj/Django/Trading_Project/trading_project/market_data/static/OpenAPIScripMaster020226.json"
    ) as f:
        for item in json.load(f):
            SCRIP_MASTER[item["token"]] = item
except Exception as e:
    logger.error(f"Failed to load Scrip Master: {e}")


# ============================================================
# SYMBOL PARSER (SOURCE OF TRUTH)
# ============================================================
OPTION_SYMBOL_REGEX = re.compile(
    r"^(?P<index>[A-Z]+)"
    r"(?P<day>\d{2})"
    r"(?P<month>[A-Z]{3})"
    r"(?P<year>\d{2})"
    r"(?P<strike>\d+)"
    r"(?P<option_type>CE|PE)$"
)


def parse_option_symbol(symbol: str):
    match = OPTION_SYMBOL_REGEX.match(symbol)
    if not match:
        return None

    return {
        "index": match.group("index"),
        "expiry": f"{match.group('day')}{match.group('month')}20{match.group('year')}",
        "strike": int(match.group("strike")),
        "option_type": match.group("option_type"),
    }

# ============================================================
# GET NEAREST FUTIDX
# ============================================================
def get_nearest_futidx(index_name: str):
    """
    Returns nearest FUTIDX row info for given index (e.g. NIFTY)
    """
    today = datetime.today().date()
    fut_rows = []

    for item in SCRIP_MASTER.values():
        if (
            item.get("instrumenttype") == "FUTIDX"
            and item.get("name", "").upper() == index_name.upper()
            and item.get("expiry")
        ):
            try:
                expiry_dt = datetime.strptime(
                    item["expiry"], "%d%b%Y"
                ).date()
            except Exception:
                continue

            if expiry_dt >= today:
                fut_rows.append((expiry_dt, item))

    if not fut_rows:
        return None

    # 🔥 nearest expiry
    expiry_dt, row = min(fut_rows, key=lambda x: x[0])

    return {
        "token": str(row["token"]),
        "symbol": row["symbol"],
        "expiry": expiry_dt.strftime("%Y-%m-%d"),
    }


# ============================================================
# EXCHANGE TYPE RESOLVER (UNCHANGED)
# ============================================================
def get_exchange_type(token):
    info = SCRIP_MASTER.get(str(token))
    if not info:
        return 2

    exch = info.get("exch_seg", "").upper()
    inst = info.get("instrumenttype", "").upper()

    if exch in ("NSE", "NFO"):
        return 2 if ("FUT" in inst or "OPT" in inst) else 1
    if exch in ("BSE", "BFO"):
        return 4 if ("FUT" in inst or "OPT" in inst) else 3
    if exch == "MCX":
        return 5
    if exch == "NCDEX":
        return 7
    if exch == "CDE":
        return 13
    

    return 2


# ============================================================
# 🔥 SPOT → OPTION TOKENS (TESTED CODE)
# ============================================================
def get_option_tokens_from_spot(index, spot_price):
    index = index.upper()
    today = datetime.today().date()

    expiries = sorted({
        item["expiry"]
        for item in SCRIP_MASTER.values()
        if item.get("instrumenttype") == "OPTIDX"
        and item.get("name", "").upper() == index
        and item.get("expiry")
    })

    parsed = [
        (datetime.strptime(exp, "%d%b%Y").date(), exp)
        for i,exp in enumerate(expiries)
    ]
    nearest_expiry = None
    parsed.sort(key=lambda x: x[0])
    for dt,exp in parsed:
        if dt >= today:
            nearest_expiry = exp
            break
    if not nearest_expiry:
        return None

    strikes = set()
    parsed_cache = []

    for item in SCRIP_MASTER.values():
        if (
            item.get("instrumenttype") == "OPTIDX"
            and item.get("name", "").upper() == index
            and item.get("expiry") == nearest_expiry
        ):
            parsed = parse_option_symbol(item["symbol"])
            if parsed:
                strikes.add(parsed["strike"])
                parsed_cache.append((parsed, item["token"]))

    strikes = sorted(strikes)
    if len(strikes) < 5:
        return None

    atm = min(strikes, key=lambda s: abs(s - spot_price))
    idx = strikes.index(atm)

    if idx < 2 or idx + 2 >= len(strikes):
        return None

    window = strikes[idx - 2 : idx + 3]

    tokens = [
        token for parsed, token in parsed_cache
        if parsed["strike"] in window
    ]

    return set(tokens) if len(tokens) == 10 else None


# ============================================================
# CONSUMER
# ============================================================
class MarketDataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_group_name = "market_data"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )

        self.ws = None
        self.msg_queue = Queue()

        # 🔥 NEW STATE
        self.index_name = "NIFTY"
        self.index_token = None
        self.current_option_tokens = set()

        threading.Thread(
            target=self.start_smartapi_websocket, daemon=True
        ).start()

    async def disconnect(self, close_code):
        if self.ws:
            self.ws.close_connection()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        tokens = data.get("tokens")

        exch_type = get_exchange_type(tokens[0])

        if action == "subscribe":
            self.ws.subscribe(
                "abc1234",
                1,
                [{"exchangeType": exch_type, "tokens": tokens}],
            )

            # 🔥 INDEX SUBSCRIBE
            info = SCRIP_MASTER.get(tokens[0])
            if info and info.get("instrumenttype") == "AMXIDX":
                self.index_token = tokens[0]

        elif action == "unsubscribe":
            self.ws.unsubscribe(
                "abc1234",
                1,
                [{"exchangeType": exch_type, "tokens": tokens}],
            )

            # 🔥 INDEX UNSUBSCRIBE → REMOVE OPTIONS
            if tokens[0] == self.index_token and self.current_option_tokens:
                self.ws.unsubscribe(
                    "abc1234",
                    1,
                    [{
                        "exchangeType": 2,
                        "tokens": list(self.current_option_tokens),
                    }],
                )
                self.current_option_tokens.clear()
                self.index_token = None

    async def send_market_data(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    # ========================================================
    # SMARTAPI WORKER
    # ========================================================
    def start_smartapi_websocket(self):
        from django.contrib.auth.models import User
        from smart_api_integration.models import UserApiCredentials, UserApiTokens

        user = User.objects.get(username="suraj")
        creds = UserApiCredentials.objects.get(user=user)
        tokens = UserApiTokens.objects.get(user=user)

        self.ws = SmartWebSocketV2(
            tokens.jwt_token,
            creds.api_key,
            creds.client_id,
            tokens.feed_token,
        )

        # 🔥 DEFAULT FUTIDX
        fut = get_nearest_futidx(self.index_name)

        self.fut_token = None
        self.fut_symbol = None
        self.fut_expiry = None

        if fut:
            self.fut_token = fut["token"]
            self.fut_symbol = fut["symbol"]
            self.fut_expiry = fut["expiry"]

            logger.info(
                f"Default FUTIDX → {self.fut_symbol} | {self.fut_expiry}"
            )

        def on_open(ws):
            sub_list = []

            # 🔥 Subscribe FUTIDX by default
            if self.fut_token:
                sub_list.append({
                    "exchangeType": 2,   # NFO
                    "tokens": [self.fut_token],
                })

            # # 🔥 Optional: also subscribe INDEX if available
            # if self.index_token:
            #     sub_list.append({
            #         "exchangeType": 1,   # NSE INDEX
            #         "tokens": [self.index_token],
            #     })

            if sub_list:
                self.ws.subscribe("abc1234", 2, sub_list)


        def on_data(ws, msg):
            print(msg)
            token = str(msg.get("token"))

            ltp = msg.get("last_traded_price")

            # 🔥 INDEX TICK → AUTO OPTION SUBSCRIBE
            if token == self.index_token:
                spot = int(round(ltp / 100))
                new_tokens = get_option_tokens_from_spot(
                    self.index_name, spot
                )

                if new_tokens and new_tokens != self.current_option_tokens:
                    if self.current_option_tokens:
                        self.ws.unsubscribe(
                            "abc1234",
                            1,
                            [{
                                "exchangeType": 2,
                                "tokens": list(self.current_option_tokens),
                            }],
                        )

                    self.ws.subscribe(
                        "abc1234",
                        1,
                        [{
                            "exchangeType": 2,
                            "tokens": list(new_tokens),
                        }],
                    )

                    self.current_option_tokens = new_tokens

            async_to_sync(get_channel_layer().group_send)(
                "market_data",
                {"type": "send_market_data", "data": msg},
            )

        self.ws.on_open = on_open
        self.ws.on_data = on_data
        self.ws.connect()
