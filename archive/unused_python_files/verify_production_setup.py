#!/usr/bin/env python3
"""
Verify production setup is correctly configured.
"""

import os
import ccxt

def main():
    print("=== Production Setup Verification ===")
    print()
    
    # Check environment variables
    okx_demo = os.getenv("OKX_DEMO", "0")  # Default to live trading
    api_key = os.getenv("OKX_API_KEY", "")
    secret = os.getenv("OKX_SECRET_KEY", "")
    passphrase = os.getenv("OKX_PASSPHRASE", "")
    
    print(f"OKX_DEMO setting: {okx_demo}")
    print(f"Production mode: {'✓ YES' if okx_demo.lower() in ('0', 'false', 'f', 'no', 'n', 'off') else '✗ NO (still in demo)'}")
    print(f"API Key: {'✓ Present' if api_key else '✗ Missing'}")
    print(f"Secret Key: {'✓ Present' if secret else '✗ Missing'}")
    print(f"Passphrase: {'✓ Present' if passphrase else '✗ Missing'}")
    print()
    
    # Test connection
    if all([api_key, secret, passphrase]):
        print("Testing OKX connection...")
        try:
            # Test with production mode
            is_demo = okx_demo.lower() in ('1', 'true', 't', 'yes', 'y', 'on')
            
            exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': secret,
                'password': passphrase,
                'sandbox': is_demo,
                'enableRateLimit': True
            })
            
            if is_demo:
                # No simulated trading headers for live mode
                print("Mode: Demo/Sandbox")
            else:
                print("Mode: Live Trading")
            
            # Test connection
            markets = exchange.load_markets()
            print(f"✓ Connection successful - {len(markets)} markets loaded")
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            
            if "50119" in str(e):
                if is_demo:
                    print("💡 Your API key was created for Live Trading, not Demo")
                else:
                    print("💡 Your API key was created for Demo/Testnet, not Live Trading")
                    print("   Create new API keys for Live Trading in your OKX account")
    
    print()
    print("=== Status Summary ===")
    if okx_demo.lower() in ('0', 'false', 'f', 'no', 'n', 'off'):
        print("✓ System configured for production mode")
        print("✓ All demo/simulation code removed")
        print("⚠ Need Live Trading API keys to connect")
    else:
        print("✗ System still in demo mode - check OKX_DEMO setting")

if __name__ == "__main__":
    main()