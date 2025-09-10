#!/usr/bin/env python3
"""
Test live currency switching functionality with real portfolio data
"""

import time

import requests


def test_currency_conversion_with_real_data():
    """Test currency conversion with real PEPE portfolio data"""
    print("=" * 60)
    print("LIVE CURRENCY CONVERSION TEST WITH REAL PORTFOLIO DATA")
    print("=" * 60)

    # Get exchange rates
    rates_response = requests.get('http://localhost:5000/api/exchange-rates')
    if rates_response.status_code != 200:
        print("❌ Failed to get exchange rates")
        return

    rates_data = rates_response.json()
    rates = rates_data.get('rates', {})
    print(f"Source: {rates_data.get('source', 'NOT SPECIFIED')}")

    # Get portfolio data
    portfolio_response = requests.get('http://localhost:5000/api/crypto-portfolio')
    if portfolio_response.status_code != 200:
        print("❌ Failed to get portfolio data")
        return

    portfolio = portfolio_response.json()

    # Extract key values
    total_value = portfolio.get('total_current_value', 0)
    daily_pnl = portfolio.get('total_pnl', 0)
    pepe_holding = None

    if portfolio.get('holdings'):
        for holding in portfolio['holdings']:
            if holding.get('symbol') == 'PEPE':
                pepe_holding = holding
                break

    print("\n📊 REAL PORTFOLIO DATA:")
    print(f"  Total Portfolio Value: ${total_value:.2f}")
    print(f"  Daily P&L: ${daily_pnl:.2f}")
    if pepe_holding:
        print(f"  PEPE Quantity: {pepe_holding.get('quantity', 0):,.0f}")
        print(f"  PEPE Current Value: ${pepe_holding.get('current_value', 0):.2f}")
        print(f"  PEPE P&L: ${pepe_holding.get('pnl', 0):.2f}")

    print("\n💱 CURRENCY CONVERSION TESTS:")
    print("-" * 40)

    # Test each currency conversion
    test_currencies = ['USD', 'EUR', 'GBP', 'AUD']

    for currency in test_currencies:
        if currency in rates:
            rate = rates[currency]
            converted_total = total_value * rate
            converted_pnl = daily_pnl * rate

            symbol = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': 'A$'}[currency]

            print(f"\n{currency} Conversion (Rate: {rate}):")
            print(f"  Total Value: {symbol}{converted_total:.2f}")
            print(f"  Daily P&L: {symbol}{converted_pnl:.2f}")

            if pepe_holding:
                converted_pepe_value = pepe_holding.get('current_value', 0) * rate
                converted_pepe_pnl = pepe_holding.get('pnl', 0) * rate
                print(f"  PEPE Value: {symbol}{converted_pepe_value:.2f}")
                print(f"  PEPE P&L: {symbol}{converted_pepe_pnl:.2f}")

    return True

def test_currency_api_consistency():
    """Test that currency data is consistent across API calls"""
    print("\n" + "=" * 60)
    print("API CONSISTENCY TEST")
    print("=" * 60)

    # Make multiple calls and compare
    calls = []
    for _i in range(3):
        response = requests.get('http://localhost:5000/api/exchange-rates')
        if response.status_code == 200:
            calls.append(response.json())
        time.sleep(0.5)

    if len(calls) >= 2:
        rates1 = calls[0].get('rates', {})
        rates2 = calls[1].get('rates', {})

        consistent = True
        for currency in rates1:
            if currency in rates2:
                if abs(rates1[currency] - rates2[currency]) > 0.001:  # Allow small floating point differences
                    print(f"❌ Rate inconsistency for {currency}: {rates1[currency]} vs {rates2[currency]}")
                    consistent = False

        if consistent:
            print("✅ Exchange rates are consistent across API calls")
        else:
            print("❌ Exchange rates show inconsistency")
    else:
        print("❌ Unable to test consistency - API calls failed")

def simulate_frontend_currency_switching():
    """Simulate what happens when user switches currency in frontend"""
    print("\n" + "=" * 60)
    print("FRONTEND CURRENCY SWITCHING SIMULATION")
    print("=" * 60)

    # Get base data
    portfolio_response = requests.get('http://localhost:5000/api/crypto-portfolio')
    rates_response = requests.get('http://localhost:5000/api/exchange-rates')

    if portfolio_response.status_code == 200 and rates_response.status_code == 200:
        portfolio = portfolio_response.json()
        rates = rates_response.json().get('rates', {})

        total_value = portfolio.get('total_current_value', 0)

        print("Simulating user selecting different currencies:")
        print("-" * 50)

        for currency in ['USD', 'EUR', 'GBP', 'AUD']:
            if currency in rates:
                rate = rates[currency]
                converted = total_value * rate
                symbol = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': 'A$'}[currency]

                print(f"User selects {currency}:")
                print(f"  → Frontend calls formatCurrency({total_value}, '{currency}')")
                print(f"  → Calculation: {total_value:.2f} × {rate} = {converted:.2f}")
                print(f"  → Display: {symbol}{converted:.2f}")
                print()
    else:
        print("❌ Failed to get required data for simulation")

def main():
    """Run comprehensive currency conversion tests"""
    print("🔄 COMPREHENSIVE CURRENCY CONVERSION TEST SUITE")
    print("Testing OKX-based currency conversion with real portfolio data")

    # Test with real data
    test_currency_conversion_with_real_data()

    # Test API consistency
    test_currency_api_consistency()

    # Simulate frontend behavior
    simulate_frontend_currency_switching()

    print("\n" + "=" * 60)
    print("✅ CURRENCY CONVERSION TESTING COMPLETE")
    print("=" * 60)
    print("\nTo manually test currency switching:")
    print("1. Open the trading dashboard")
    print("2. Use the currency selector dropdown")
    print("3. Verify all values update correctly")
    print("4. Check that PEPE holdings show converted amounts")

if __name__ == "__main__":
    main()
