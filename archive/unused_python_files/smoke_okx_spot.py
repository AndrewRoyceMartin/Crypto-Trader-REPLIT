#!/usr/bin/env python3
"""
Minimal OKX spot smoke test:
- Verifies connection (demo/live)
- Loads markets
- Prints a couple of tickers
- Shows a tiny spot account summary
"""

import os
import sys
import traceback

from src.exchanges.okx_adapter_spot import make_okx_spot, spot_summary


def main() -> None:
    ex = make_okx_spot()

    # ccxt uses set_sandbox_mode; attribute is 'sandboxMode' (not 'sandbox')
    sandbox_mode = bool(getattr(ex, "sandboxMode", False))
    print("Connected to OKX (spot). Sandbox mode:", sandbox_mode)

    # Ensure markets are loaded and handle Optional typing cleanly
    try:
        ex.load_markets()
    except Exception as e:
        print("load_markets failed:", e)
        raise

    markets_count = len(ex.markets or {})
    print("Markets loaded:", markets_count)

    # Check a couple of common markets
    for sym in ("BTC/USDT", "ETH/USDT"):
        try:
            t = ex.fetch_ticker(sym)
            last = t.get("last")
            print(f"{sym} last:", last)
        except Exception as e:
            print(f"{sym} unavailable:", e)

    # Print simple summary (balances + open orders)
    try:
        s = spot_summary(ex)
        print("=== Spot Summary ===")
        print("Base Currency:", s.get("base_currency"))
        print("Balances:", s.get("balances"))
        print("Open Orders:", s.get("open_orders"))
    except Exception as e:
        print("spot_summary failed:", e)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Smoke test failed:", exc)
        print(traceback.format_exc())
        sys.exit(1)
