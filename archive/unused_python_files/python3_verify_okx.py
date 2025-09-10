#!/usr/bin/env python3
import os, time, ccxt

def make_okx():
    ex = ccxt.okx({
        'enableRateLimit': True,
        'apiKey': os.getenv('OKX_API_KEY'),
        'secret': os.getenv('OKX_API_SECRET'),
        'password': os.getenv('OKX_API_PASSPHRASE'),
    })
    demo = str(os.getenv('OKX_DEMO', '0')).strip() in ('1','true','True','yes','on')
    ex.set_sandbox_mode(demo)

    # Remove simulated header if live
    if not demo and ex.headers:
        ex.headers.pop('x-simulated-trading', None)

    # Sanity prints
    print("ccxt version:", ccxt.__version__)
    print("Mode:", "DEMO" if demo else "LIVE")
    print("Key present:", bool(ex.apiKey), "Passphrase present:", bool(ex.password))

    return ex

def main():
    ex = make_okx()
    ex.verbose = False  # set True to see raw requests/responses

    # 1) Public endpoint should work regardless of auth
    markets = ex.load_markets()
    print("Markets loaded:", len(markets))

    # 2) Auth endpoint – if this fails with 501xx, it’s an auth/permission/whitelist/time issue
    try:
        bal = ex.fetch_balance()
        usdt = bal.get('USDT', {})
        print("Balance USDT free:", usdt.get('free'), " total:", usdt.get('total'))
    except Exception as e:
        print("fetch_balance failed:", repr(e))
        # common root causes
        print("\nTroubleshooting:")
        print("  - Ensure OKX_DEMO matches your key (demo vs live)")
        print("  - Re-check API key/secret/passphrase (exact, case-sensitive, no whitespace)")
        print("  - Make sure env vars are QUOTED (especially if they contain #, +, /, =)")
        print("  - If you enabled IP whitelist on the key, add this server’s IP or disable whitelist")
        print("  - Give the key READ/TRADE permissions as needed")
        print("  - Check server clock is in sync (ntp). Skew >30s can break signatures.")
        return

    # 3) Tiny trade simulation check (no order placement)
    try:
        t = ex.fetch_ticker('BTC/USDT')
        print("BTC/USDT last:", t.get('last'))
    except Exception as e:
        print("fetch_ticker failed:", repr(e))

if __name__ == "__main__":
    main()
