#!/usr/bin/env python3
"""
OKX Data Comparison Tool
Compares what the app shows vs what your actual OKX account contains.
"""

import os
from datetime import datetime

import ccxt
import requests


def test_okx_direct():
    """Test OKX connection directly."""
    print("=" * 60)
    print("DIRECT OKX ACCOUNT DATA")
    print("=" * 60)

    try:
        # Get credentials
        api_key = os.getenv('OKX_API_KEY', '')
        secret = os.getenv('OKX_SECRET_KEY', '')
        passphrase = os.getenv('OKX_PASSPHRASE', '')
        hostname = os.getenv('OKX_HOSTNAME', 'www.okx.com')

        if not all([api_key, secret, passphrase]):
            print("❌ Missing OKX credentials")
            return

        # Connect to OKX
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret,
            'password': passphrase,
            'hostname': hostname,
            'sandbox': False,
            'enableRateLimit': True,
        })

        exchange.load_markets()
        print("✅ Successfully connected to OKX")

        # Get balance
        balance = exchange.fetch_balance()

        print("\n📊 Raw Balance Data:")
        crypto_balances = {}
        for key, value in balance.items():
            if (key not in ['info', 'timestamp', 'datetime', 'free', 'used', 'total']
                and isinstance(value, dict)
                and value.get('total', 0) > 0):
                crypto_balances[key] = value
                print(f"  {key}: {value}")

        # Get positions
        positions = exchange.fetch_positions()
        active_positions = [pos for pos in positions if pos['contracts'] > 0]
        print(f"\n📈 Active Positions: {len(active_positions)}")
        for pos in active_positions[:3]:  # First 3
            print(f"  {pos['symbol']}: {pos['contracts']} contracts")

        # Get current PEPE price
        try:
            ticker = exchange.fetch_ticker('PEPE/USDT')
            pepe_price = ticker['last']
            print(f"\n💰 Current PEPE/USDT Price: ${pepe_price:.8f}")
        except Exception as e:
            print(f"\n❌ Could not get PEPE price: {e}")
            pepe_price = 0.00001  # Fallback

        return crypto_balances, pepe_price

    except Exception as e:
        print(f"❌ OKX connection error: {e}")
        return {}, 0

def test_app_api():
    """Test what the app's API returns."""
    print("\n" + "=" * 60)
    print("APP API DATA")
    print("=" * 60)

    try:
        response = requests.get('http://localhost:5000/api/crypto-portfolio', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully fetched app data")

            print("\n📊 App Portfolio Summary:")
            print(f"  Total Value: ${data.get('total_current_value', 0):.2f}")
            print(f"  Total P&L: ${data.get('total_pnl', 0):.2f}")
            print(f"  P&L %: {data.get('total_pnl_percent', 0):.2f}%")
            print(f"  Cash Balance: ${data.get('cash_balance', 0):.2f}")

            print(f"\n📈 Holdings ({len(data.get('holdings', []))}):")
            for holding in data.get('holdings', []):
                print(f"  {holding['symbol']}:")
                print(f"    Quantity: {holding['quantity']:,.2f}")
                print(f"    Current Price: ${holding['current_price']:.8f}")
                print(f"    Current Value: ${holding['current_value']:.2f}")
                print(f"    Cost Basis: ${holding['cost_basis']:.2f}")
                print(f"    Avg Entry: ${holding['avg_entry_price']:.8f}")
                print(f"    P&L: ${holding['pnl']:.2f} ({holding['pnl_percent']:.2f}%)")

            return data
        else:
            print(f"❌ App API error: {response.status_code}")
            return {}

    except Exception as e:
        print(f"❌ App API connection error: {e}")
        return {}

def compare_data(okx_data, okx_price, app_data):
    """Compare OKX data with app data."""
    print("\n" + "=" * 60)
    print("DATA COMPARISON")
    print("=" * 60)

    if not okx_data or not app_data:
        print("❌ Missing data for comparison")
        return

    print("\n🔍 PEPE Comparison:")

    # OKX data
    okx_pepe = okx_data.get('PEPE', {})
    okx_quantity = okx_pepe.get('total', 0)
    okx_free = okx_pepe.get('free', 0)

    print("  OKX Account:")
    print(f"    Quantity: {okx_quantity:,.8f}")
    print(f"    Free: {okx_free:,.8f}")
    print(f"    Current Price: ${okx_price:.8f}")
    print(f"    Current Value: ${okx_quantity * okx_price:.2f}")

    # App data
    app_holdings = app_data.get('holdings', [])
    pepe_holding = next((h for h in app_holdings if h['symbol'] == 'PEPE'), None)

    if pepe_holding:
        print("  App Data:")
        print(f"    Quantity: {pepe_holding['quantity']:,.8f}")
        print(f"    Current Price: ${pepe_holding['current_price']:.8f}")
        print(f"    Current Value: ${pepe_holding['current_value']:.2f}")
        print(f"    Cost Basis: ${pepe_holding['cost_basis']:.2f}")
        print(f"    Avg Entry: ${pepe_holding['avg_entry_price']:.8f}")

        # Check for differences
        print("\n✅ Differences:")
        qty_diff = abs(okx_quantity - pepe_holding['quantity'])
        price_diff = abs(okx_price - pepe_holding['current_price'])

        if qty_diff < 0.00000001:
            print(f"    Quantity: ✅ MATCH ({qty_diff:.10f} difference)")
        else:
            print(f"    Quantity: ❌ MISMATCH ({qty_diff:.10f} difference)")

        if price_diff < 0.00000001:
            print(f"    Price: ✅ MATCH ({price_diff:.10f} difference)")
        else:
            print(f"    Price: ❌ MISMATCH ({price_diff:.10f} difference)")

        # Calculate expected value
        expected_value = okx_quantity * okx_price
        actual_value = pepe_holding['current_value']
        value_diff = abs(expected_value - actual_value)

        if value_diff < 0.01:
            print(f"    Value: ✅ MATCH (${value_diff:.4f} difference)")
        else:
            print(f"    Value: ❌ MISMATCH (${value_diff:.4f} difference)")

    else:
        print("  ❌ No PEPE holding found in app data")

def main():
    """Run the data comparison."""
    print("🚀 OKX Data Comparison Tool")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test OKX directly
    okx_data, okx_price = test_okx_direct()

    # Test app API
    app_data = test_app_api()

    # Compare the data
    compare_data(okx_data, okx_price, app_data)

    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print("If all checks show ✅ MATCH, then the app data IS matching your OKX account.")
    print("If you see ❌ MISMATCH, that indicates the specific discrepancy.")
    print("\n💡 TIP: Check your OKX web interface to verify the expected values.")

if __name__ == "__main__":
    main()
