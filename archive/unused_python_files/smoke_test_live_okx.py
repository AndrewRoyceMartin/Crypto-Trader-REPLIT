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
    raise SystemExit("Missing OKX_API_KEY / OKX_API_SECRET(or OKX_SECRET_KEY) / OKX_API_PASSPHRASE(or OKX_PASSPHRASE)")

ex = ccxt.okx({
    'enableRateLimit': True,
    'apiKey': api_key,
    'secret': secret,
    'password': passwd,
})

# FORCE LIVE
ex.set_sandbox_mode(False)
if ex.headers:
    ex.headers.pop('x-simulated-trading', None)

print("Sandbox mode:", getattr(ex, 'sandboxMode', False))
print("Headers:", ex.headers)

# Public works without auth
print("Base URL:", ex.urls.get('api'))
print("BTC/USDT last:", ex.fetch_ticker('BTC/USDT').get('last'))

# Private requires valid LIVE keys (no sandbox header)
bal = ex.fetch_balance()
print("USDT free:", bal.get('USDT', {}).get('free'))
