"""
Fetches OHLCV candles from Binance Spot's public REST API.
No API key needed — read-only public market data, same market the user trades.

V1 uses REST polling (see scanner.py's background loop) rather than a raw
Binance WebSocket connection — simpler to run reliably, and at a 60s scan
interval the data is effectively live for swing-style decisions. A true
WebSocket feed (lower latency, push-based) is a reasonable V2 upgrade if
you want tighter timing later.
"""

import requests
from config import BINANCE_BASE_URL


def validate_symbols(symbols):
    """
    Checks which symbols are actually active on Binance Spot.
    Returns (valid, invalid) lists. One bad symbol never blocks the rest.
    """
    try:
        resp = requests.get(f"{BINANCE_BASE_URL}/api/v3/exchangeInfo", timeout=15)
        resp.raise_for_status()
        info = resp.json()
        active = {
            s["symbol"] for s in info["symbols"]
            if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"
        }
    except Exception as e:
        print(f"[binance] exchangeInfo failed ({e}) — skipping validation, using list as-is")
        return symbols, []

    valid = [s for s in symbols if s in active]
    invalid = [s for s in symbols if s not in active]
    return valid, invalid


def get_klines(symbol, interval="1h", limit=220):
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    raw = resp.json()

    candles = []
    for row in raw:
        candles.append({
            "open_time": row[0],
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        })
    return candles


def get_klines_batch(symbols, interval="1h", limit=220, max_workers=10):
    """
    Fetches candles for many symbols in parallel (Binance's public rate limit
    comfortably allows this at ~240 symbols). A failed symbol is skipped, not fatal.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results, failed = {}, []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_symbol = {
            pool.submit(get_klines, symbol, interval, limit): symbol
            for symbol in symbols
        }
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                results[symbol] = future.result()
            except Exception as e:
                failed.append((symbol, str(e)))
    return results, failed
