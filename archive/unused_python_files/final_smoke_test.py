#!/usr/bin/env python3
import os, ccxt

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

print("=== CLEAN OKX SMOKE TEST ===")
print(f"API Key: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
print(f"Secret: {secret[:4]}...{secret[-4:]} ({len(secret)} chars)")
print(f"Passphrase: {'*' * len(passwd)} ({len(passwd)} chars)")
print()

def test_mode(mode_name, sandbox_mode):
    print(f"--- Testing {mode_name} Mode ---")
    ex = ccxt.okx({
        'enableRateLimit': True,
        'apiKey': api_key,
        'secret': secret,
        'password': passwd,
    })
    
    # Set mode
    ex.set_sandbox_mode(sandbox_mode)
    if ex.headers:
        ex.headers.pop('x-simulated-trading', None)
    
    print(f"Sandbox mode: {getattr(ex, 'sandboxMode', False)}")
    print(f"Headers: {ex.headers}")
    print(f"Base URL: {ex.urls.get('api', {}).get('rest', 'unknown')}")
    
    try:
        # Try private call
        bal = ex.fetch_balance()
        print(f"✅ {mode_name} SUCCESS - Balance fetched")
        print(f"USDT free: {bal.get('USDT', {}).get('free', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ {mode_name} FAILED: {str(e)}")
        return False

# Test both modes
live_works = test_mode("LIVE", False)
print()
demo_works = test_mode("DEMO", True)

print()
print("=== SUMMARY ===")
print(f"Live Trading: {'✅ WORKS' if live_works else '❌ FAILED'}")
print(f"Demo Trading: {'✅ WORKS' if demo_works else '❌ FAILED'}")

if demo_works and not live_works:
    print("\n🔍 DIAGNOSIS: API keys work for DEMO only")
    print("ACTION: Create new API keys for Live Trading in OKX account")
elif live_works:
    print("\n✅ READY: API keys work for Live Trading")
else:
    print("\n❌ ISSUE: API keys don't work for either mode")