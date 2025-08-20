# verify_okx.py
import os, ccxt

def _getenv(*names, default=None):
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default

ex = ccxt.okx({
    'enableRateLimit': True,
    'apiKey': _getenv('OKX_API_KEY'),
    'secret': _getenv('OKX_API_SECRET', 'OKX_SECRET_KEY'),
    'password': _getenv('OKX_API_PASSPHRASE', 'OKX_PASSPHRASE'),
})

demo = str(os.getenv("OKX_DEMO", "1")).strip().lower() in ("1","true","t","yes","y","on")
ex.set_sandbox_mode(demo)
if demo and ex.headers:
    ex.headers["x-simulated-trading"] = "1"

ex.load_markets()
bal = ex.fetch_balance()
print("Markets:", len(ex.markets))
print("USDT free:", bal.get('USDT', {}).get('free'))
print("BTC/USDT last:", ex.fetch_ticker('BTC/USDT')['last'])
