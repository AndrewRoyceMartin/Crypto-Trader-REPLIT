# src/exchanges/okx_adapter_spot.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import ccxt


def _truthy(v: Optional[str]) -> bool:
    return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")


def make_okx_spot() -> ccxt.okx:
    """
    Return a ccxt OKX client configured for SPOT. Supports both live and demo (sandbox).
    Env vars supported:
      OKX_API_KEY, OKX_API_SECRET|OKX_SECRET_KEY, OKX_API_PASSPHRASE|OKX_PASSPHRASE, OKX_DEMO
    """
    api_key = os.getenv("OKX_API_KEY")
    api_secret = os.getenv("OKX_API_SECRET") or os.getenv("OKX_SECRET_KEY")
    passphrase = os.getenv("OKX_API_PASSPHRASE") or os.getenv("OKX_PASSPHRASE")
    use_demo = _truthy(os.getenv("OKX_DEMO", "1"))  # default ON for safety

    ex = ccxt.okx({
        "enableRateLimit": True,
        "apiKey": api_key,
        "secret": api_secret,
        "password": passphrase,
    })

    # DEMO / Sandbox
    ex.set_sandbox_mode(use_demo)
    if use_demo:
        # required for demo on OKX
        ex.headers = {**(ex.headers or {}), "x-simulated-trading": "1"}
    else:
        # ensure no simulated header leaks into live
        if ex.headers:
            ex.headers.pop("x-simulated-trading", None)

    # Force SPOT
    ex.options = {**getattr(ex, "options", {}), "defaultType": "spot"}

    # Load markets once here so callers don't forget
    ex.load_markets()
    return ex
