#!/usr/bin/env python3
"""
Apply the regional endpoint fix automatically.
Sets OKX_HOSTNAME=app.okx.com and tests the connection.
"""
import os

# Set the regional endpoint
os.environ["OKX_HOSTNAME"] = "app.okx.com"

print("=== APPLYING REGIONAL ENDPOINT FIX ===")
print("Setting OKX_HOSTNAME=app.okx.com")
print()

# Test the fix using our updated adapter
try:
    from src.exchanges.okx_adapter_spot import make_okx_spot
    
    print("Creating OKX connection with regional endpoint...")
    ex = make_okx_spot()
    
    print(f"✅ Connection created successfully")
    print(f"Hostname: {getattr(ex, 'hostname', 'default')}")
    print(f"Sandbox mode: {getattr(ex, 'sandboxMode', False)}")
    print(f"Headers: {ex.headers}")
    print()
    
    print("Testing API connection...")
    balance = ex.fetch_balance()
    
    print("🎉 SUCCESS! OKX connection working with regional endpoint!")
    print(f"Account has {len([k for k, v in balance.items() if isinstance(v, dict) and v.get('total', 0) > 0])} assets")
    
    # Show some key balances
    for symbol in ['USDT', 'BTC', 'ETH']:
        if symbol in balance and isinstance(balance[symbol], dict):
            free = balance[symbol].get('free', 0)
            total = balance[symbol].get('total', 0)
            if total > 0:
                print(f"{symbol}: {free} free, {total} total")
    
    print("\n✅ Regional endpoint fix successful!")
    print("The system is now ready for live trading.")
    
except Exception as e:
    error_msg = str(e)
    print(f"❌ Still having issues: {error_msg}")
    
    if "50110" in error_msg:
        print("\n💡 IP whitelist issue - your key works but IP is blocked")
        print("Add 34.148.21.249 to your OKX API key whitelist")
        print("Or disable IP whitelist completely")
    elif "50119" in error_msg:
        print("\n💡 Still wrong endpoint or credential issue")
    else:
        print(f"\n💡 Different error: {error_msg}")

print(f"\n🔧 To make this permanent, add OKX_HOSTNAME=app.okx.com to your Replit Secrets")