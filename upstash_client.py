"""
Thin client for Upstash Redis's REST API. Serverless functions have no
memory between invocations, so this is where scan results, the active
timeframe, and Telegram alert history actually live between runs.

Free tier: 10,000 commands/day, far more than this app needs even scanning
every few minutes.
"""

import json
import requests

from config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN


def _command(*args):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        raise RuntimeError("Upstash not configured — set UPSTASH_REDIS_REST_URL / _TOKEN in Vercel env vars")

    resp = requests.post(
        UPSTASH_REDIS_URL,
        headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
        json=list(args),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("result")


def set_json(key, obj):
    _command("SET", key, json.dumps(obj))


def get_json(key, default=None):
    raw = _command("GET", key)
    if raw is None:
        return default
    return json.loads(raw)
