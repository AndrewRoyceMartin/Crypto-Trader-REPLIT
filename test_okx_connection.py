#!/usr/bin/env python3
"""Test OKX API connection with current credentials."""

import os
import ccxt

def test_okx_connection():
    """Test OKX API connection with current environment variables."""
    
    api_key = os.getenv('OKX_API_KEY', '')
    secret_key = os.getenv('OKX_SECRET_KEY', '')
    passphrase = os.getenv('OKX_PASSPHRASE', '')
    
    print("=== OKX Connection Test ===")
    print(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else 'TOO SHORT'}")
    print(f"Secret: {'*' * len(secret_key)} ({len(secret_key)} chars)")
    print(f"Passphrase: {'*' * len(passphrase)} ({len(passphrase)} chars)")
    
    if not all([api_key, secret_key, passphrase]):
        print("❌ Missing credentials!")
        return False
    
    try:
        print("\n🔄 Testing OKX connection...")
        
        # Create exchange instance
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'sandbox': False,  # Live trading
            'enableRateLimit': True,
            'timeout': 30000,
            'verbose': False
        })
        
        # Test 1: Load markets (public endpoint)
        print("📊 Testing market data access...")
        markets = exchange.load_markets()
        print(f"✅ Markets loaded successfully: {len(markets)} trading pairs")
        
        # Test 2: Get account balance (private endpoint)
        print("💰 Testing account access...")
        balance = exchange.fetch_balance()
        
        # Count currencies with balances
        currencies_with_balance = 0
        total_usd_value = 0.0
        
        for currency, info in balance.items():
            if isinstance(info, dict) and info.get('total', 0) > 0:
                currencies_with_balance += 1
                if currency == 'USDT':
                    total_usd_value += info.get('total', 0)
        
        print(f"✅ Account access successful!")
        print(f"   - Currencies with balances: {currencies_with_balance}")
        print(f"   - USDT balance: ${total_usd_value:.2f}")
        
        # Test 3: Check trading permissions
        print("🔑 Testing trading permissions...")
        try:
            # Try to get positions (requires trading permissions)
            positions = exchange.fetch_positions()
            print(f"✅ Trading permissions verified: {len(positions)} positions")
        except Exception as e:
            print(f"⚠️  Trading permissions limited: {e}")
        
        print("\n🎉 OKX connection test PASSED!")
        return True
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify API key is from live OKX account (not demo)")
        print("   2. Check API key permissions include 'Trade' and 'Read'")
        print("   3. Verify passphrase matches exactly (case-sensitive)")
        print("   4. Check IP whitelist allows current IP")
        return False
        
    except ccxt.NetworkError as e:
        print(f"❌ Network Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check internet connection")
        print("   2. Verify OKX API is accessible from your location")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    test_okx_connection()