"""
Sends a Telegram alert only when a coin NEWLY enters an important setup
category. State is kept in Upstash (not memory) since serverless functions
don't persist between invocations.
"""

import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ALERT_SETUP_TYPES, ALERT_MIN_SCORE
from upstash_client import get_json, set_json

ALERT_STATE_KEY = "alerted_state"


def send_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[telegram] send failed: {e}")


def check_and_alert(results):
    last_alerted = get_json(ALERT_STATE_KEY, default={})
    changed = False

    for r in results:
        symbol = r["symbol"]
        qualifies = r["setup_type"] in ALERT_SETUP_TYPES and r["score"] >= ALERT_MIN_SCORE
        previously_alerted = last_alerted.get(symbol) == r["setup_type"]

        if qualifies and not previously_alerted:
            reasons = "\n".join(f"✓ {reason}" for reason in r["reasons"])
            text = (
                f"*{r['setup_type']} — {symbol}*\n"
                f"Setup Score: {r['score']}/100\n\n"
                f"{reasons}\n\n"
                f"_This is a technical setup summary, not a probability of profit. "
                f"Do your own check before acting._"
            )
            send_message(text)
            last_alerted[symbol] = r["setup_type"]
            changed = True
        elif not qualifies and symbol in last_alerted:
            del last_alerted[symbol]
            changed = True

    if changed:
        set_json(ALERT_STATE_KEY, last_alerted)
