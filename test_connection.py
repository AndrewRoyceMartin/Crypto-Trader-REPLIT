#!/usr/bin/env python3
"""Test OKX connection with current setup."""

import sys
import os
sys.path.append('.')

try:
    from src.exchanges.okx_adapter import make_okx_spot
    
    print("=== Testing OKX Connection ===")
    print()
    
    # Check environment
    api_key = os.getenv("OKX_API_KEY", "")
    secret_key = os.getenv("OKX_SECRET_KEY", "")
    passphrase = os.getenv("OKX_PASSPHRASE", "")
    demo_mode = os.getenv("OKX_DEMO", "1")
    
    print(f"OKX_DEMO: {demo_mode}")
    print(f"Production mode: {'YES' if demo_mode.lower() in ('0', 'false', 'f', 'no', 'n', 'off') else 'NO'}")
    print(f"API Key: {'Present' if api_key else 'Missing'}")
    print(f"Secret Key: {'Present' if secret_key else 'Missing'}")
    print(f"Passphrase: {'Present' if passphrase else 'Missing'}")
    print()
    
    if not all([api_key, secret_key, passphrase]):
        print("❌ Missing credentials - cannot test connection")
        sys.exit(1)
    
    print("Testing connection...")
    try:
        exchange = make_okx_spot()
        print("✅ Connection successful!")
        print(f"Loaded {len(exchange.markets)} markets")
        
        # Test basic functionality
        ticker = exchange.fetch_ticker('BTC/USDT')
        print(f"BTC/USDT price: ${ticker['last']}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        if "50119" in str(e):
            print("\n💡 Your API keys may be for Demo/Testnet, not Live Trading")
            print("   Create new API keys for Live Trading in your OKX account")
        
        sys.exit(1)

except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)