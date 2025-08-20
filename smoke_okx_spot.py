#!/usr/bin/env python3
import os, sys, traceback

# Ensure project root on sys.path (useful on some hosts)
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.exchanges.okx_adapter_spot import make_okx_spot, spot_summary

def main():
    # Expect env vars:
    #   OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE
    #   OKX_SANDBOX=1 for demo / 0 for live
    ex = make_okx_spot()
    print("Connected to OKX (spot). Sandbox:", ex.sandbox)
    print("Markets loaded:", len(ex.markets))

    # Check a couple of common markets
    for sym in ("BTC/USDT", "ETH/USDT"):
        try:
            t = ex.fetch_ticker(sym)
            print(f"{sym} last:", t.get("last"))
        except Exception as e:
            print(f"{sym} unavailable:", e)

    # Print simple summary (balances + open orders)
    s = spot_summary(ex)
    print("=== Spot Summary ===")
    print("Base Currency:", s["base_currency"])
    print("Balances:", s["balances"])
    print("Open Orders:", s["open_orders"])

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Smoke test failed:", e)
        print(traceback.format_exc())
        sys.exit(1)
