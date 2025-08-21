#!/usr/bin/env python3
"""
Test the regional endpoint fix based on the 50110 vs 50119 error pattern.
The US endpoint (app.okx.com) returned 50110 (IP whitelist), not 50119 (key doesn't exist).
This suggests the API key works on app.okx.com but not other endpoints.
"""
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

print("=== REGIONAL FIX TEST ===")
print("Based on diagnostic: app.okx.com gave 50110 (IP whitelist) not 50119 (key missing)")
print("This suggests the API key is region-locked to the US endpoint.")
print()

# Set the hostname to test app.okx.com with IP whitelist fix
os.environ["OKX_HOSTNAME"] = "app.okx.com"
print(f"Setting OKX_HOSTNAME=app.okx.com")

# Now test our updated adapter
from src.exchanges.okx_adapter_spot import make_okx_spot

try:
    print("Testing with regional endpoint fix...")
    ex = make_okx_spot()
    
    print(f"Hostname: {getattr(ex, 'hostname', 'not set')}")
    print(f"Sandbox mode: {getattr(ex, 'sandboxMode', False)}")
    print(f"Headers: {ex.headers}")
    
    # Test connection
    print("Attempting to fetch balance...")
    bal = ex.fetch_balance()
    
    print("✅ SUCCESS! Regional endpoint fix worked!")
    print(f"Total assets: {len([k for k, v in bal.items() if isinstance(v, dict) and v.get('total', 0) > 0])}")
    
    if 'USDT' in bal:
        print(f"USDT free: {bal['USDT']['free']}")
    
except Exception as e:
    error_msg = str(e)
    print(f"❌ Still failed: {error_msg}")
    
    if "50110" in error_msg:
        print("\n💡 This confirms the key works on app.okx.com but IP is blocked")
        print("Solution: Add Replit's IP (35.229.97.108) to your API key whitelist")
        print("Or disable IP whitelist completely in your OKX API settings")
    elif "50119" in error_msg:
        print("\n💡 Key still doesn't exist on this endpoint")
        print("Try a different regional endpoint or create new keys")
    else:
        print(f"\n💡 Different error: {error_msg}")

print(f"\nCurrent test IP: Check your OKX API whitelist settings")