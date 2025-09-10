#!/usr/bin/env python3
"""
Debug OKX Trade History - Test different methods to fetch recent trades
"""

import os
from datetime import datetime, timedelta

import ccxt


def test_okx_trade_methods():
    """Test different OKX methods to find recent trades."""

    try:
        # Initialize OKX exchange
        exchange = ccxt.okx({
            'apiKey': os.getenv('OKX_API_KEY'),
            'secret': os.getenv('OKX_SECRET_KEY'),
            'password': os.getenv('OKX_PASSPHRASE'),
            'sandbox': False,
            'enableRateLimit': True
        })

        print("=== OKX Trade History Debug Test ===")
        print(f"Connected to OKX: {exchange.id}")

        # Test 1: fetch_my_trades with no parameters
        print("\n1. Testing fetch_my_trades()...")
        try:
            trades = exchange.fetch_my_trades(limit=50)
            print(f"   Result: {len(trades)} trades found")
            if trades:
                latest = trades[0]
                print(f"   Latest trade: {latest['symbol']} - {latest['side']} - {latest['amount']} @ {latest['price']}")
                print(f"   Timestamp: {latest['datetime']}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 2: fetch_my_trades for specific symbols
        symbols = ['PEPE/USDT', 'BTC/USDT']
        for symbol in symbols:
            print(f"\n2. Testing fetch_my_trades('{symbol}')...")
            try:
                trades = exchange.fetch_my_trades(symbol, limit=20)
                print(f"   Result: {len(trades)} trades for {symbol}")
                if trades:
                    latest = trades[0]
                    print(f"   Latest: {latest['side']} {latest['amount']} @ {latest['price']} on {latest['datetime']}")
            except Exception as e:
                print(f"   Error: {e}")

        # Test 3: fetch_orders (all orders)
        print("\n3. Testing fetch_orders()...")
        try:
            orders = exchange.fetch_orders(limit=20)
            print(f"   Result: {len(orders)} orders found")
            if orders:
                latest = orders[0]
                print(f"   Latest order: {latest['symbol']} - {latest['side']} - {latest['amount']} @ {latest['price']}")
                print(f"   Status: {latest['status']} - {latest['datetime']}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 4: fetch_closed_orders
        print("\n4. Testing fetch_closed_orders()...")
        try:
            closed = exchange.fetch_closed_orders(limit=20)
            print(f"   Result: {len(closed)} closed orders found")
            if closed:
                latest = closed[0]
                print(f"   Latest closed: {latest['symbol']} - {latest['side']} - {latest['amount']} @ {latest['price']}")
                print(f"   Status: {latest['status']} - {latest['datetime']}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 5: fetch_orders with time range (last 7 days)
        print("\n5. Testing fetch_orders with time range...")
        try:
            since = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            orders = exchange.fetch_orders(since=since, limit=50)
            print(f"   Result: {len(orders)} orders in last 7 days")
            if orders:
                for order in orders[:3]:  # Show first 3
                    print(f"   - {order['symbol']} {order['side']} {order['amount']} @ {order['price']} ({order['status']}) - {order['datetime']}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 6: Check account info
        print("\n6. Testing account balance...")
        try:
            balance = exchange.fetch_balance()
            print(f"   Balance keys: {list(balance.keys())}")
            for key, value in balance.items():
                if isinstance(value, dict) and 'total' in value and value['total'] > 0:
                    print(f"   {key}: {value}")
        except Exception as e:
            print(f"   Error: {e}")

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"OKX connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    test_okx_trade_methods()
