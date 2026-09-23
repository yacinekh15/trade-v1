"""Config for the all-Vercel Halal Crypto Scanner (serverless + Upstash Redis)."""

import os

BINANCE_BASE_URL = "https://api.binance.com"
COINS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coins.txt")
CANDLE_LOOKBACK = 220

TIMEFRAMES = ["5m", "15m", "1h", "4h"]
DEFAULT_TIMEFRAME = "1h"

# Telegram alerts (optional) — set in Vercel's Environment Variables, not here.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ALERT_SETUP_TYPES = {"BREAKOUT", "MOMENTUM"}
ALERT_MIN_SCORE = 70

# Upstash Redis (free tier) — set in Vercel's Environment Variables.
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

# Shared secret so only your scheduler (not randoms) can trigger a scan.
SCAN_SECRET = os.environ.get("SCAN_SECRET", "")


def load_coins(path=COINS_FILE):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]
