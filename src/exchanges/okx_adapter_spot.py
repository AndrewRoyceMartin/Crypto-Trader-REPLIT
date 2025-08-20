# -*- coding: utf-8 -*-
"""
OKX Spot adapter (ccxt-based)

Reads env vars (both common variants supported):
- OKX_API_KEY
- OKX_API_SECRET  or OKX_SECRET_KEY
- OKX_API_PASSPHRASE or OKX_PASSPHRASE
- OKX_DEMO (default: "1" -> demo/sandbox mode)
- OKX_SPOT_SYMBOL (default: "BTC/USDT")
"""

from __future__ import annotations

import os
import typing as t

import ccxt  # type: ignore


def _env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "t", "yes", "y", "on")


def _get_okx_creds() -> dict:
    # Support both naming styles
    api_key = os.getenv("OKX_API_KEY") or ""
    secret = os.getenv("OKX_API_SECRET") or os.getenv("OKX_SECRET_KEY") or ""
    passphrase = os.getenv("OKX_API_PASSPHRASE") or os.getenv("OKX_PASSPHRASE") or ""

    return {
        "apiKey": api_key,
        "secret": secret,
        "password": passphrase,  # ccxt expects 'password' for OKX passphrase
    }


def make_okx_spot(demo: t.Optional[bool] = None) -> ccxt.okx:
    """
    Build a ccxt.okx client configured for SPOT trading.
    If demo is None, it reads OKX_DEMO env (default True).
    """
    if demo is None:
        demo = _env_bool("OKX_DEMO", True)

    creds = _get_okx_creds()
    ex = ccxt.okx({
        "enableRateLimit": True,
        **creds,
        "options": {
            "defaultType": "spot",   # ensure SPOT (not swap/futures)
            "defaultMarket": "spot",
        },
    })

    # Always use live trading mode - no sandbox/demo support
    ex.set_sandbox_mode(False)
    # Ensure no simulated headers
    if ex.headers:
        ex.headers.pop("x-simulated-trading", None)

    return ex


def spot_summary(ex: ccxt.okx, symbol: t.Optional[str] = None) -> dict:
    """
    Return a small summary: markets count, balance snapshot, and a ticker.
    """
    ex.load_markets()

    # symbol default: env var or BTC/USDT
    symbol = symbol or os.getenv("OKX_SPOT_SYMBOL") or "BTC/USDT"

    # balances (spot)
    bal = ex.fetch_balance()  # OKX returns a normalized balance dict
    # Try to extract a clean free/total USDT if present
    usdt_free = (bal.get("USDT") or {}).get("free") if isinstance(bal.get("USDT"), dict) else None
    usdt_total = (bal.get("USDT") or {}).get("total") if isinstance(bal.get("USDT"), dict) else None

    # Ticker
    ticker = ex.fetch_ticker(symbol)

    return {
        "demo": ex.options.get("sandboxMode", False) or ("x-simulated-trading" in (ex.headers or {})),
        "markets": len(ex.markets),
        "symbol": symbol,
        "usdt_free": usdt_free,
        "usdt_total": usdt_total,
        "ticker_last": ticker.get("last"),
        "raw_balance": bal,  # keep raw for debugging
    }
