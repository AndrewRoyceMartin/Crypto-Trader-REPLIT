#!/usr/bin/env python3
"""
Debug OKX API Permissions and Account Info
"""

import os

import ccxt


def debug_okx_permissions():
    """Check OKX API permissions and capabilities."""

    try:
        # Initialize OKX exchange
        exchange = ccxt.okx({
            'apiKey': os.getenv('OKX_API_KEY'),
            'secret': os.getenv('OKX_SECRET_KEY'),
            'password': os.getenv('OKX_PASSPHRASE'),
            'sandbox': False,
            'enableRateLimit': True
        })

        print("=== OKX API Permissions & Account Debug ===")

        # 1. Check account info
        print("\n1. Account Info:")
        try:
            account = exchange.fetch_balance()
            print(f"   Account type: {account.get('info', {}).get('details', [{}])[0].get('ccy', 'Unknown')}")
            print(f"   Available currencies: {[k for k, v in account.items() if isinstance(v, dict) and v.get('total', 0) > 0]}")
        except Exception as e:
            print(f"   Error: {e}")

        # 2. Check trading permissions
        print("\n2. Trading Capabilities:")

        # Test different trading pairs
        test_symbols = ['PEPE/USDT', 'BTC/USDT', 'ETH/USDT']
        for symbol in test_symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                print(f"   ✓ Can access {symbol} market data (price: ${ticker['last']})")
            except Exception as e:
                print(f"   ✗ Cannot access {symbol}: {e}")

        # 3. Check order history methods
        print("\n3. Order History Methods:")

        methods_to_test = [
            ('fetch_my_trades', lambda: exchange.fetch_my_trades(limit=1)),
            ('fetch_closed_orders', lambda: exchange.fetch_closed_orders(limit=1)),
            ('fetch_open_orders', lambda: exchange.fetch_open_orders()),
        ]

        for method_name, method_func in methods_to_test:
            try:
                result = method_func()
                print(f"   ✓ {method_name}: Returns {len(result)} items")
            except Exception as e:
                print(f"   ✗ {method_name}: {e}")

        # 4. Check specific symbol history
        print("\n4. Symbol-Specific History:")
        for symbol in ['PEPE/USDT', 'BTC/USDT']:
            try:
                trades = exchange.fetch_my_trades(symbol, limit=5)
                print(f"   {symbol}: {len(trades)} trades")

                orders = exchange.fetch_closed_orders(symbol, limit=5)
                print(f"   {symbol}: {len(orders)} closed orders")
            except Exception as e:
                print(f"   {symbol} error: {e}")

        # 5. Check permissions with smaller limits
        print("\n5. Testing with minimal limits:")
        try:
            tiny_trades = exchange.fetch_my_trades(limit=1)
            print(f"   fetch_my_trades(limit=1): {len(tiny_trades)} trades")
        except Exception as e:
            print(f"   fetch_my_trades(limit=1) error: {e}")

        # 6. Check account trading history directly
        print("\n6. Account Trading Activity:")
        try:
            # Sometimes OKX has account-level endpoints
            if hasattr(exchange, 'fetch_ledger'):
                ledger = exchange.fetch_ledger(limit=10)
                print(f"   Ledger entries: {len(ledger)}")
                if ledger:
                    print(f"   Latest ledger entry: {ledger[0].get('type', 'unknown')} - {ledger[0].get('amount', 0)}")
        except Exception as e:
            print(f"   Ledger check error: {e}")

        print("\n=== Debug Complete ===")
        print("\nSUMMARY:")
        print("- If all methods return 0 trades but you made purchases, the issue could be:")
        print("  1. API permissions don't include trade history access")
        print("  2. Trades were made on a different account/subaccount")
        print("  3. Trades are too old (beyond API retention period)")
        print("  4. Trades were made via a different method (web, mobile app)")
        print("  5. OKX API doesn't sync immediately with recent purchases")

    except Exception as e:
        print(f"OKX connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    debug_okx_permissions()
