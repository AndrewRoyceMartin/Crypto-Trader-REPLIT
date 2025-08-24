#!/usr/bin/env python3
"""
Test live OKX API connection with detailed error analysis.
"""

import os
import ccxt
import json
from datetime import datetime

def test_okx_connection():
    """Test OKX connection with detailed diagnostics."""
    print("=== OKX Live API Connection Test ===")
    print(f"Test time: {datetime.now()}")
    print()
    
    # Get credentials
    api_key = os.getenv("OKX_API_KEY", "")
    secret_key = os.getenv("OKX_SECRET_KEY", "")
    passphrase = os.getenv("OKX_PASSPHRASE", "")
    
    print("Credential Check:")
    print(f"API Key: {'✓ Present' if api_key else '✗ Missing'} ({len(api_key)} chars)")
    print(f"Secret Key: {'✓ Present' if secret_key else '✗ Missing'} ({len(secret_key)} chars)")
    print(f"Passphrase: {'✓ Present' if passphrase else '✗ Missing'} ({len(passphrase)} chars)")
    print()
    
    if not all([api_key, secret_key, passphrase]):
        print("❌ Missing credentials - cannot proceed")
        return False
    
    # Test live trading connection only
    mode_name = "Live Trading"
    sandbox_mode = False
    print(f"Testing {mode_name} Mode:")
    print("-" * 30)
    
    try:
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'sandbox': sandbox_mode,
            'enableRateLimit': True,
            'timeout': 15000
        })
        
        # Ensure no simulated trading headers
        if exchange.headers:
            exchange.headers.pop('x-simulated-trading', None)
        
        print(f"Exchange initialized: ✓")
        print(f"Sandbox mode: {sandbox_mode}")
        base_url = exchange.urls.get('api', 'Unknown') if exchange.urls else 'Unknown'
        print(f"Base URL: {base_url}")
        
        # Test basic connection
        print("Testing connection...")
        markets = exchange.load_markets()
        print(f"✓ Connected successfully")
        print(f"✓ Markets loaded: {len(markets)} trading pairs")
        
        # Test account access
        print("Testing account access...")
        balance = exchange.fetch_balance()
        print(f"✓ Account access successful")
        
        # Show some balance info (without exposing amounts)
        currencies = list(balance.get('total', {}).keys())
        print(f"✓ Found balances for {len(currencies)} currencies")
        
        # Test positions (spot trading)
        try:
            positions = exchange.fetch_positions()
            print(f"✓ Positions query successful: {len(positions)} positions")
        except Exception as pos_error:
            print(f"⚠ Positions query failed: {pos_error}")
        
        print(f"🎉 {mode_name} connection successful!")
        return True
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ {mode_name} connection failed: {error_msg}")
        
        # Analyze error
        if "50119" in error_msg:
            print("💡 Analysis: API key doesn't exist in this environment")
            if not sandbox_mode:
                print("   → Your API key was likely created for Demo/Testnet, not Live Trading")
                print("   → Create new API keys specifically for Live Trading in OKX")
            else:
                print("   → Your API key was likely created for Live Trading, not Demo")
        elif "50113" in error_msg:
            print("💡 Analysis: Invalid API key format or credentials")
        elif "50102" in error_msg:
            print("💡 Analysis: Timestamp error - check system time")
        elif "50103" in error_msg:
            print("💡 Analysis: Invalid signature - check secret key")
        elif "50111" in error_msg:
            print("💡 Analysis: Invalid passphrase")
        elif "50112" in error_msg:
            print("💡 Analysis: IP not whitelisted")
            print("   → Add this IP to your OKX API whitelist: 35.229.97.108")
        
        print()
        return False
    
    print("=== Next Steps ===")
    print("If Live Trading failed but Demo worked:")
    print("1. Log into your OKX account")
    print("2. Go to API Management")
    print("3. Create NEW API keys for 'Live Trading' (not Demo)")
    print("4. Set permissions: Read + Trade")
    print("5. Add IP to whitelist: 35.229.97.108")
    print("6. For Australia: Ensure ASIC compliance verification is complete")
    print()
    print("If both failed:")
    print("1. Check API key format (36 chars)")
    print("2. Check secret key format (32 chars)")
    print("3. Verify passphrase is correct")
    print("4. Ensure IP is whitelisted: 35.229.97.108")

if __name__ == "__main__":
    test_okx_connection()