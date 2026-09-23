"""
Vercel serverless API for the Halal Crypto Scanner.
"""

import sys
import os
import time
import traceback

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fastapi import FastAPI, Query

app = FastAPI()

CURRENT_TIMEFRAME_KEY = "current_timeframe"


# ---------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------

def get_dependencies():
    try:
        from config import (
            load_coins,
            TIMEFRAMES,
            DEFAULT_TIMEFRAME,
            CANDLE_LOOKBACK,
            SCAN_SECRET,
        )

        from scanner import run_scan
        from telegram_alerts import check_and_alert
        from upstash_client import get_json, set_json

        return {
            "load_coins": load_coins,
            "TIMEFRAMES": TIMEFRAMES,
            "DEFAULT_TIMEFRAME": DEFAULT_TIMEFRAME,
            "CANDLE_LOOKBACK": CANDLE_LOOKBACK,
            "SCAN_SECRET": SCAN_SECRET,
            "run_scan": run_scan,
            "check_and_alert": check_and_alert,
            "get_json": get_json,
            "set_json": set_json,
        }

    except Exception as e:
        print("DEPENDENCY IMPORT ERROR:")
        traceback.print_exc()
        raise


def results_key(timeframe):
    return f"results:{timeframe}"


def do_scan(timeframe):
    deps = get_dependencies()

    symbols = deps["load_coins"]()

    results, failed = deps["run_scan"](
        symbols,
        timeframe,
        deps["CANDLE_LOOKBACK"]
    )

    payload = {
        "timeframe": timeframe,
        "updated_at": time.time(),
        "results": results,
        "failed_count": len(failed),
    }

    deps["set_json"](
        results_key(timeframe),
        payload
    )

    deps["check_and_alert"](results)

    return payload


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "python": sys.version,
    }


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

@app.get("/api/results")
async def api_results(
    timeframe: str = None
):
    deps = get_dependencies()

    if timeframe is None:
        timeframe = deps["DEFAULT_TIMEFRAME"]

    if timeframe not in deps["TIMEFRAMES"]:
        return {
            "error": f"timeframe must be one of {deps['TIMEFRAMES']}"
        }

    cached = deps["get_json"](
        results_key(timeframe)
    )

    if cached is None:
        return {
            "status": "no_results",
            "timeframe": timeframe,
            "updated_at": None,
            "results": [],
            "failed_count": 0,
            "message": "No scan has been completed yet. Trigger the scanner from GitHub Actions or POST /api/scan.",
        }

    return cached


# ---------------------------------------------------------
# Scan
# ---------------------------------------------------------

@app.post("/api/scan")
async def api_scan(
    secret: str = Query(default="")
):
    deps = get_dependencies()

    if deps["SCAN_SECRET"] and secret != deps["SCAN_SECRET"]:
        return {
            "error": "invalid secret"
        }

    timeframe = deps["get_json"](
        CURRENT_TIMEFRAME_KEY,
        default=deps["DEFAULT_TIMEFRAME"]
    )

    payload = do_scan(timeframe)

    return {
        "ok": True,
        "timeframe": timeframe,
        "num_results": len(payload["results"]),
    }


# ---------------------------------------------------------
# Timeframe
# ---------------------------------------------------------

@app.post("/api/timeframe")
async def set_timeframe(
    timeframe: str = Query(...)
):
    deps = get_dependencies()

    if timeframe not in deps["TIMEFRAMES"]:
        return {
            "error": f"timeframe must be one of {deps['TIMEFRAMES']}"
        }

    deps["set_json"](
        CURRENT_TIMEFRAME_KEY,
        timeframe
    )

    return {
        "ok": True,
        "current_timeframe": timeframe,
    }
