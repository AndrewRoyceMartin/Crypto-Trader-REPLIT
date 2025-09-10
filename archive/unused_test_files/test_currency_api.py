#!/usr/bin/env python3
"""
Test currency conversion functionality
"""


import requests


def test_exchange_rates():
    """Test the exchange rates API"""
    print("=" * 50)
    print("TESTING EXCHANGE RATES API")
    print("=" * 50)

    response = requests.get('http://localhost:5000/api/exchange-rates')
    if response.status_code == 200:
        data = response.json()
        print("✅ Exchange rates API working")
        print(f"Source: {data.get('source', 'NOT SPECIFIED')}")
        print(f"Base: {data.get('base', 'N/A')}")
        print("Rates:")
        for currency, rate in data.get('rates', {}).items():
            print(f"  {currency}: {rate}")
        return data.get('rates', {})
    else:
        print(f"❌ Exchange rates API failed: {response.status_code}")
        return {}

def test_portfolio_data():
    """Test portfolio data API"""
    print("\n" + "=" * 50)
    print("TESTING PORTFOLIO DATA API")
    print("=" * 50)

    response = requests.get('http://localhost:5000/api/crypto-portfolio')
    if response.status_code == 200:
        data = response.json()
        print("✅ Portfolio API working")
        print(f"Total Value: ${data.get('total_value', 0):.2f}")
        print(f"Daily P&L: ${data.get('daily_pnl', 0):.2f}")
        print(f"Cash Balance: ${data.get('cash_balance', 0):.2f}")
        return data
    else:
        print(f"❌ Portfolio API failed: {response.status_code}")
        return {}

def test_currency_conversion(rates, portfolio_data):
    """Test currency conversion calculations"""
    print("\n" + "=" * 50)
    print("TESTING CURRENCY CONVERSION")
    print("=" * 50)

    test_usd_amount = portfolio_data.get('total_value', 100.0)

    for currency, rate in rates.items():
        if currency != 'USD':
            converted = test_usd_amount * rate
            print(f"\n{currency} Conversion Test:")
            print(f"  USD Amount: ${test_usd_amount:.2f}")
            print(f"  Exchange Rate: {rate}")
            print(f"  {currency} Amount: {currency_symbol(currency)}{converted:.2f}")

            # Test formatCurrency-like behavior
            formatted = f"{currency_symbol(currency)}{converted:,.2f}"
            print(f"  Formatted: {formatted}")

def currency_symbol(currency):
    """Get currency symbol"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'AUD': 'A$'
    }
    return symbols.get(currency, currency + ' ')

def test_frontend_currency_switching():
    """Test that frontend currency switching works"""
    print("\n" + "=" * 50)
    print("TESTING FRONTEND CURRENCY SWITCHING")
    print("=" * 50)

    # Test if the main dashboard loads
    response = requests.get('http://localhost:5000/')
    if response.status_code == 200:
        html = response.text
        if 'currency-selector' in html:
            print("✅ Currency selector found in frontend")
        else:
            print("❌ Currency selector not found in frontend")

        if 'fetchExchangeRates' in html:
            print("✅ Exchange rate fetching function found")
        else:
            print("❌ Exchange rate fetching function not found")

        if 'formatCurrency' in html:
            print("✅ Currency formatting function found")
        else:
            print("❌ Currency formatting function not found")
    else:
        print(f"❌ Frontend failed to load: {response.status_code}")

def main():
    """Run all currency conversion tests"""
    print("CURRENCY CONVERSION TEST SUITE")
    print("Testing OKX-based currency conversion system")

    # Test APIs
    rates = test_exchange_rates()
    portfolio_data = test_portfolio_data()

    # Test conversion calculations
    if rates and portfolio_data:
        test_currency_conversion(rates, portfolio_data)

    # Test frontend
    test_frontend_currency_switching()

    print("\n" + "=" * 50)
    print("CURRENCY CONVERSION TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
