#!/usr/bin/env python3
import os

import ccxt


def env_first(*keys):
    for k in keys:
        v = os.getenv(k)
        if v and str(v).strip():
            return str(v).strip()
    return None

api_key = env_first("OKX_API_KEY")
secret  = env_first("OKX_API_SECRET", "OKX_SECRET_KEY")
passwd  = env_first("OKX_API_PASSPHRASE", "OKX_PASSPHRASE")

if not (api_key and secret and passwd):
    raise SystemExit("Missing OKX credentials")

print("=== OKX REGIONAL ENDPOINT TESTING (2024 Fix) ===")
print(f"API Key: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
print()

# Known OKX regional endpoints based on 2024 updates
endpoints = {
    'global_www': 'www.okx.com',     # Default global
    'regional_my': 'my.okx.com',     # EEA/Regional endpoint (key fix!)
    'us_app': 'app.okx.com',         # US endpoint
    'direct': 'okx.com',             # Direct domain
}

def test_endpoint(name, hostname):
    print(f"--- Testing {name.upper()} ({hostname}) ---")
    try:
        ex = ccxt.okx({
            'enableRateLimit': True,
            'apiKey': api_key,
            'secret': secret,
            'password': passwd,
            'hostname': hostname,  # This is the key parameter!
        })

        # Force live trading mode
        ex.set_sandbox_mode(False)
        if ex.headers:
            ex.headers.pop('x-simulated-trading', None)

        print(f"Hostname: {hostname}")
        print(f"Sandbox mode: {getattr(ex, 'sandboxMode', False)}")
        print(f"Headers: {ex.headers}")

        # Try private API call
        bal = ex.fetch_balance()
        print(f"✅ {name.upper()} SUCCESS - Balance fetched")

        # Show some balance details
        if 'USDT' in bal:
            print(f"USDT free: {bal['USDT']['free']}")
        if 'BTC' in bal:
            print(f"BTC free: {bal['BTC']['free']}")

        return True, hostname
    except Exception as e:
        error_msg = str(e)
        if "50119" in error_msg:
            print(f"❌ {name.upper()} - 50119 (API key doesn't exist)")
        elif "DNS" in error_msg or "resolve" in error_msg.lower():
            print(f"❌ {name.upper()} - DNS/Network error")
        elif "timeout" in error_msg.lower():
            print(f"❌ {name.upper()} - Timeout")
        else:
            print(f"❌ {name.upper()} - {error_msg}")
        return False, hostname

# Test each endpoint
results = {}
working_endpoint = None

for name, hostname in endpoints.items():
    success, host = test_endpoint(name, hostname)
    results[name] = success
    if success and not working_endpoint:
        working_endpoint = host
    print()

print("=== SUMMARY ===")
for endpoint, works in results.items():
    status = '✅ WORKS' if works else '❌ FAILED'
    print(f"{endpoint.upper()}: {status}")

if working_endpoint:
    print(f"\n🎯 WORKING ENDPOINT FOUND: {working_endpoint}")
    print(f"Use this in your CCXT configuration: hostname='{working_endpoint}'")

    # Generate the fix code
    print("\n=== IMPLEMENTATION FIX ===")
    print("Add this to your OKX adapter:")
    print(f"""
ex = ccxt.okx({{
    'enableRateLimit': True,
    'hostname': '{working_endpoint}',  # <-- Regional fix
    'apiKey': api_key,
    'secret': secret,
    'password': passphrase,
}})
""")
else:
    print("\n❌ No working endpoints found")
    print("This suggests the API credentials themselves need to be recreated")
    print("or there's an account-level issue (verification, restrictions, etc.)")
