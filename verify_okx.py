import os, ccxt

def env(name: str) -> str | None:
    return os.getenv(name)

API_KEY     = env('OKX_API_KEY')
SECRET      = env('OKX_SECRET_KEY') or env('OKX_API_SECRET')
PASSPHRASE  = env('OKX_PASSPHRASE') or env('OKX_API_PASSPHRASE')

def show_env():
    print("ENV:")
    print("  OKX_API_KEY       :", "OK" if API_KEY else "MISSING", "len=", len(API_KEY or ""))
    print("  OKX_SECRET_KEY    :", "OK" if os.getenv('OKX_SECRET_KEY') else "MISSING")
    print("  OKX_API_SECRET    :", "OK" if os.getenv('OKX_API_SECRET') else "MISSING")
    print("  OKX_PASSPHRASE    :", "OK" if os.getenv('OKX_PASSPHRASE') else "MISSING")
    print("  OKX_API_PASSPHRASE:", "OK" if os.getenv('OKX_API_PASSPHRASE') else "MISSING")

def try_okx(sandbox: bool):
    label = "SANDBOX" if sandbox else "PROD"
    print(f"\n== {label} ==")
    ex = ccxt.okx({
        'enableRateLimit': True,
        'apiKey': API_KEY,
        'secret': SECRET,
        'password': PASSPHRASE,
    })
    # Always use live trading mode - no sandbox support
    ex.set_sandbox_mode(False)
    # Ensure no simulated headers
    if ex.headers:
        ex.headers.pop('x-simulated-trading', None)

    # Public – should always work
    try:
        t = ex.fetch_ticker('BTC/USDT')
        print("  Public OK. BTC/USDT last:", t.get('last'))
    except Exception as e:
        print("  Public FAIL:", type(e).__name__, str(e))

    # Private – validates the keys
    try:
        bal = ex.fetch_balance()
        usdt = (bal.get('USDT') or {})
        print("  Private OK. USDT free:", usdt.get('free'), "total:", usdt.get('total'))
    except Exception as e:
        msg = str(e)
        print("  Private FAIL:", type(e).__name__, msg)
        if "50119" in msg:
            print("   Hint: 50119 = key doesn’t exist in this environment (Demo vs Prod mismatch).")
        if "50113" in msg:
            print("   Hint: 50113 = IP not whitelisted (Prod). Either whitelist or use Sandbox.")

if __name__ == "__main__":
    show_env()
    try_okx(False)  # LIVE TRADING ONLY
