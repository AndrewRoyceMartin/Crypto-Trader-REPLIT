#!/usr/bin/env python3
"""
Deployment verification script to check if all components are working correctly.
"""

import json
import sys
from datetime import datetime

import requests


def check_endpoint(url, timeout=10):
    """Check if an endpoint is responding correctly."""
    try:
        print(f"Checking {url}...")
        response = requests.get(url, timeout=timeout)
        status_code = response.status_code

        if status_code == 200:
            print(f"✓ {url} - Status: {status_code}")
            return True
        else:
            print(f"✗ {url} - Status: {status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ {url} - Error: {e}")
        return False

def check_json_endpoint(url, timeout=10):
    """Check if a JSON endpoint is responding with valid data."""
    try:
        print(f"Checking JSON endpoint {url}...")
        response = requests.get(url, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ {url} - Status: {response.status_code}, Data keys: {list(data.keys())}")
            return True, data
        else:
            print(f"✗ {url} - Status: {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"✗ {url} - Error: {e}")
        return False, None
    except json.JSONDecodeError as e:
        print(f"✗ {url} - JSON decode error: {e}")
        return False, None

def main():
    """Run deployment verification checks."""
    print("=" * 60)
    print("DEPLOYMENT VERIFICATION SCRIPT")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    base_url = "http://localhost:5000"

    # Health check endpoints
    health_endpoints = [
        "/",
        "/health",
        "/ready"
    ]

    # API endpoints to test
    api_endpoints = [
        "/api/crypto-portfolio",
        "/api/price-source-status",
        "/api/price-validation-status"
    ]

    all_passed = True

    print("1. Testing Health Check Endpoints")
    print("-" * 40)
    for endpoint in health_endpoints:
        url = f"{base_url}{endpoint}"
        if not check_endpoint(url):
            all_passed = False

    print("\n2. Testing API Endpoints")
    print("-" * 40)
    for endpoint in api_endpoints:
        url = f"{base_url}{endpoint}"
        success, data = check_json_endpoint(url)
        if not success:
            all_passed = False
        elif endpoint == "/api/crypto-portfolio" and data:
            # Check if portfolio has data
            crypto_count = len(data.get('cryptocurrencies', []))
            print(f"   Portfolio contains {crypto_count} cryptocurrencies")

            # Check if price validation is working
            price_validation = data.get('price_validation', {})
            live_prices = price_validation.get('live_prices', 0)
            total_symbols = price_validation.get('total_symbols', 0)
            print(f"   Price validation: {live_prices}/{total_symbols} live prices")

    print("\n3. Testing Price API Connection")
    print("-" * 40)
    success, status_data = check_json_endpoint(f"{base_url}/api/price-source-status")
    if success and status_data:
        connection_status = status_data.get('status', 'unknown')
        uptime = status_data.get('connection_uptime_seconds', 0)
        print(f"   CoinGecko API Status: {connection_status}")
        print(f"   Connection Uptime: {uptime} seconds")

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        print("The application is running correctly and all endpoints are responsive.")
    else:
        print("✗ SOME CHECKS FAILED - REVIEW BEFORE DEPLOYMENT")
        print("Please fix the issues above before deploying.")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
