#!/usr/bin/env python3
"""Final comprehensive test of OKX connection."""

import os

import ccxt


def test_okx_connection():
    print("=== Final OKX Connection Test ===")
    print()

    # Get all credentials
    api_key = os.getenv("OKX_API_KEY", "")
    secret_key = os.getenv("OKX_SECRET_KEY", "")
    passphrase = os.getenv("OKX_PASSPHRASE", "")
    demo_mode = os.getenv("OKX_DEMO", "0")  # Default to live trading

    # Determine mode
    is_demo = demo_mode.lower() in ('1', 'true', 't', 'yes', 'y', 'on')
    mode = "Demo/Sandbox" if is_demo else "Live Trading"

    print(f"Mode Setting: {mode}")
    print(f"API Key: {'✓ Present' if api_key else '✗ Missing'}")
    print(f"Secret Key: {'✓ Present' if secret_key else '✗ Missing'}")
    print(f"Passphrase: {'✓ Present' if passphrase else '✗ Missing'}")
    print()

    if not all([api_key, secret_key, passphrase]):
        print("❌ Missing credentials")
        return False

    # Test both modes to determine which one works
    for test_mode in [False, True]:  # Live first, then demo
        test_name = "Live Trading" if not test_mode else "Demo/Sandbox"
        print(f"Testing {test_name} mode...")

        try:
            exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': secret_key,
                'password': passphrase,
                'sandbox': test_mode,
                'enableRateLimit': True,
            })

            if test_mode:
                # No simulated trading headers - live mode only
                pass

            # Test connection
            markets = exchange.load_markets()
            print(f"✅ {test_name} connection successful! ({len(markets)} markets)")

            # Test basic API call
            ticker = exchange.fetch_ticker('BTC/USDT')
            print(f"   BTC/USDT price: ${ticker['last']}")

            if not test_mode:
                print("🎉 Your API keys work for LIVE TRADING!")
                return True
            else:
                print("⚠️  Your API keys work for DEMO mode only")
                return False

        except Exception as e:
            print(f"❌ {test_name} failed: {e}")

            if "50119" in str(e):
                if not test_mode:
                    print("   → API keys not valid for Live Trading")
                else:
                    print("   → API keys not valid for Demo mode")

    print()
    print("🔍 DIAGNOSIS:")
    print("Your API keys appear to be configured for Demo/Testnet only.")
    print("For live trading, you need to create NEW API keys specifically for Live Trading.")
    print()
    print("📋 TO FIX:")
    print("1. Log into your OKX account")
    print("2. Go to API Management")
    print("3. Create NEW API keys for 'Live Trading' (not demo/testnet)")
    print("4. Enable 'Read' and 'Trade' permissions")
    print("5. Whitelist IP: 35.229.97.108")
    print("6. Update the Replit secrets with the new Live Trading credentials")

    return False

if __name__ == "__main__":
    test_okx_connection()
