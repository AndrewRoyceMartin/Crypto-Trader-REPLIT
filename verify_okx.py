import os, ccxt

ex = ccxt.okx({
    'enableRateLimit': True,
    'apiKey': os.getenv('OKX_API_KEY'),
    'secret': os.getenv('OKX_API_SECRET'),
    'password': os.getenv('OKX_API_PASSPHRASE'),
})
# Live mode (set OKX_DEMO=0)
ex.set_sandbox_mode(False)
if getattr(ex, 'headers', None):
    ex.headers.pop('x-simulated-trading', None)

ex.load_markets()
print("Markets:", len(ex.markets))
bal = ex.fetch_balance()
usdt = bal.get('USDT', {}) if isinstance(bal, dict) else {}
print("USDT - free:", usdt.get('free'), " total:", usdt.get('total'))
print("BTC/USDT last:", ex.fetch_ticker('BTC/USDT')['last'])
