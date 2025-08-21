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

print("=== MYOKX INSTANTIATION TEST ===")
print(f"CCXT Version: {ccxt.__version__}")
print(f"API Key: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
print(f"Secret: {secret[:4]}...{secret[-4:]} ({len(secret)} chars)")
print(f"Passphrase: {'*' * len(passwd)} ({len(passwd)} chars)")
print()

def test_exchange_type(exchange_name, constructor):
    print(f"--- Testing {exchange_name} ---")
    try:
        ex = constructor({
            'enableRateLimit': True,
            'apiKey': api_key,
            'secret': secret,
            'password': passwd,
        })
        
        # Force live trading mode
        ex.set_sandbox_mode(False)
        if ex.headers:
            ex.headers.pop('x-simulated-trading', None)
        
        print(f"Sandbox mode: {getattr(ex, 'sandboxMode', False)}")
        print(f"Headers: {ex.headers}")
        print(f"Base URL: {ex.urls.get('api', {}).get('rest', 'unknown')}")
        
        # Try private call
        bal = ex.fetch_balance()
        print(f"✅ {exchange_name} SUCCESS - Balance fetched")
        print(f"USDT free: {bal.get('USDT', {}).get('free', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ {exchange_name} FAILED: {str(e)}")
        return False

# Test both okx and myokx (if available)
results = {}

# Test standard okx
results['okx'] = test_exchange_type("OKX", ccxt.okx)
print()

# Test myokx if available
try:
    if hasattr(ccxt, 'myokx'):
        results['myokx'] = test_exchange_type("MYOKX", ccxt.myokx)
    else:
        print("--- MYOKX not available in this CCXT version ---")
        results['myokx'] = False
except Exception as e:
    print(f"--- MYOKX instantiation failed: {e} ---")
    results['myokx'] = False

print()
print("=== SUMMARY ===")
for exchange, works in results.items():
    print(f"{exchange.upper()}: {'✅ WORKS' if works else '❌ FAILED'}")

if any(results.values()):
    print("\n✅ At least one instantiation method works!")
else:
    print("\n❌ Both methods failed - API credential issue confirmed")