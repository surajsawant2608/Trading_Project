import redis
import json
from logzero import logger

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def ltp_listener(token_risk_managers):
    pubsub = r.pubsub()
    pubsub.subscribe('ltp_updates')
    logger.info("📡 Subscribed to Redis channel: ltp_updates")

    for message in pubsub.listen():
        if message['type'] != 'message':
            continue

        try:
            data = json.loads(message['data'])

            token = str(data.get("token"))  # ensure it's string to match keys
            ltp = data.get("last_traded_price")

            if not token or ltp is None:
                logger.warning(f"⚠️ Invalid LTP message: {data}")
                continue

            ltp = float(ltp / 100)

            if token in token_risk_managers:
                manager = token_risk_managers[token]
                manager.process_price(ltp)
            else:
                pass
                # logger.info(f"ℹ️ No RiskManager registered for token {token}")

        except Exception as e:
            logger.error(f"⚠️ Error processing LTP update: {e}")
