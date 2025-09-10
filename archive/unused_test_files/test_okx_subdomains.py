#!/usr/bin/env python3
import os

import ccxt


def env_first(*keys):
    for k in keys:
        v = os.getenv(k)
        if v and str(v).strip():
            return str(v).strip()
    return None

api_key = env_first("OKX_API_KEY")
secret  = env_first("OKX_API_SECRET", "OKX_SECRET_KEY")
passwd  = env_first("OKX_API_PASSPHRASE", "OKX_PASSPHRASE")

if not (api_key and secret and passwd):
    raise SystemExit("Missing OKX credentials")

print("=== OKX SUBDOMAIN TESTING ===")
print(f"API Key: {api_key[:8]}...{api_key[-4:]} ({len(api_key)} chars)")
print()

# Known OKX subdomains for different regions
subdomains = {
    'global': 'www.okx.com',
    'australia': 'www.okx.com/au',  # Potential Australian endpoint
    'eea': 'www.okx.com/eu',        # EEA endpoint
    'aws': 'aws.okx.com',           # AWS region
    'alt1': 'okx.com',              # Alternative
}

def test_subdomain(name, base_url):
    print(f"--- Testing {name.upper()} ({base_url}) ---")
    try:
        ex = ccxt.okx({
            'enableRateLimit': True,
            'apiKey': api_key,
            'secret': secret,
            'password': passwd,
        })

        # Force live trading mode
        ex.set_sandbox_mode(False)
        if ex.headers:
            ex.headers.pop('x-simulated-trading', None)

        # Override the base URL
        if 'urls' not in ex.urls:
            ex.urls = {'api': {}}
        if 'api' not in ex.urls:
            ex.urls['api'] = {}

        # Try different URL patterns
        ex.urls['api']['rest'] = f"https://{base_url}/api/v5"

        print(f"Testing URL: {ex.urls['api']['rest']}")

        # Try private call
        bal = ex.fetch_balance()
        print(f"✅ {name.upper()} SUCCESS - Balance fetched")
        print(f"USDT free: {bal.get('USDT', {}).get('free', 'N/A')}")
        return True
    except Exception as e:
        error_msg = str(e)
        if "50119" in error_msg:
            print(f"❌ {name.upper()} - 50119 (API key doesn't exist)")
        elif "DNS" in error_msg or "resolve" in error_msg.lower():
            print(f"❌ {name.upper()} - DNS/Network error")
        elif "timeout" in error_msg.lower():
            print(f"❌ {name.upper()} - Timeout")
        else:
            print(f"❌ {name.upper()} - {error_msg}")
        return False

# Test each subdomain
results = {}
for name, subdomain in subdomains.items():
    results[name] = test_subdomain(name, subdomain)
    print()

print("=== SUMMARY ===")
for subdomain, works in results.items():
    print(f"{subdomain.upper()}: {'✅ WORKS' if works else '❌ FAILED'}")

working_subdomains = [k for k, v in results.items() if v]
if working_subdomains:
    print(f"\n✅ Working subdomain(s): {', '.join(working_subdomains)}")
else:
    print("\n❌ No subdomains worked - may need manual URL configuration")
