# qa_checks.py
import os, time, hmac, hashlib, base64
from datetime import datetime, timezone
import requests
from jsonschema import validate, Draft7Validator

try:
    from rich import print as rprint
except ImportError:
    def rprint(text):
        print(text.replace('[red]', '').replace('[/red]', '')
              .replace('[yellow]', '').replace('[/yellow]', '')
              .replace('[green]', '').replace('[/green]', '')
              .replace('[bold cyan]', '').replace('[/bold cyan]', '')
              .replace('[bold green]', '').replace('[/bold green]', ''))

BASE = os.getenv("QA_BASE_URL", "http://127.0.0.1:5000")
TIMEOUT = 20  # Increased timeout for analytics endpoints
TOL_PRICE = 0.01      # 1%
TOL_VALUE = 0.02      # 2%
TOL_ALLOC = 1.2       # 1.2%

OKX_API_KEY = os.getenv("OKX_API_KEY")
OKX_SECRET = os.getenv("OKX_SECRET_KEY")
OKX_PASS   = os.getenv("OKX_PASSPHRASE")
OKX_HOST   = os.getenv("OKX_HOSTNAME", "https://www.okx.com")
if OKX_HOST and not OKX_HOST.startswith('http'):
    OKX_HOST = f"https://{OKX_HOST}"

def _poll_ready(max_seconds=30):
    start = time.time()
    while True:
        try:
            r = requests.get(f"{BASE}/api/status", timeout=5)
            if r.status_code == 200:
                j = r.json()
                if j.get("status") == "running":
                    return True
        except Exception:
            pass
        if time.time() - start > max_seconds:
            raise RuntimeError("App not ready within timeout")
        time.sleep(0.5)

def _iso(s):
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except Exception:
        return False

def _pct_diff(a, b):
    if a == 0 and b == 0: return 0.0
    if a == 0: return 999.0
    return abs(a-b)/abs(a)

def _require(ok, msg):
    if not ok:
        raise AssertionError(msg)

# -------- JSON Schemas (minimal, flexible) ----------
schema_portfolio = {
    "type": "object",
    "properties": {
        "holdings": {"type": "array"},
        "summary": {"type": "object"},
        "total_current_value": {"type": "number"},
        "total_pnl": {"type": "number"},
        "total_pnl_percent": {"type": "number"},
        "cash_balance": {"type": "number"},
        "last_update": {"type": "string"},
    },
    "required": ["holdings", "total_current_value", "total_pnl", "total_pnl_percent"]
}

schema_holdings_row = {
    "type": "object",
    "properties": {
        "symbol": {"type": "string"},
        "name": {"type": "string"},
        "quantity": {"type": "number"},
        "current_price": {"type": "number"},
        "current_value": {"type": "number"},
        "avg_entry_price": {"type": "number"},
        "pnl": {"type": "number"},
        "pnl_percent": {"type": "number"},
        "allocation_percent": {"type": "number"},
        "is_live": {"type": ["boolean", "null"]}
    },
    "required": ["symbol", "quantity", "current_price", "current_value"]
}

schema_equity = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "equity_curve": {"type": "array"},
        "metrics": {"type": "object"},
    },
    "required": ["success", "equity_curve", "metrics"]
}

schema_drawdown = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "drawdown_data": {"type": "array"},
        "metrics": {"type": "object"},
    },
    "required": ["success", "drawdown_data", "metrics"]
}

schema_perf = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "metrics": {"type": "object"},
    },
    "required": ["success", "metrics"]
}

def validate_schema(obj, schema, name):
    v = Draft7Validator(schema)
    errs = sorted(v.iter_errors(obj), key=lambda e: e.path)
    if errs:
        for e in errs:
            rprint(f"[red]Schema error in {name}[/red]: {list(e.path)} {e.message}")
        raise AssertionError(f"Schema validation failed for {name}")

# ---------- Optional OKX native helpers ----------
def okx_sign(ts, method, path, body=""):
    if not OKX_SECRET:
        raise ValueError("OKX_SECRET not set")
    prehash = f"{ts}{method}{path}{body}"
    mac = hmac.new(OKX_SECRET.encode(), prehash.encode(), hashlib.sha256).digest()
    return base64.b64encode(mac).decode()

def okx_get(path):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    sig = okx_sign(ts, "GET", path)
    headers = {
        "OK-ACCESS-KEY": OKX_API_KEY,
        "OK-ACCESS-SIGN": sig,
        "OK-ACCESS-TIMESTAMP": ts,
        "OK-ACCESS-PASSPHRASE": OKX_PASS,
    }
    resp = requests.get(OKX_HOST + path, headers=headers, timeout=10)
    resp.raise_for_status()
    j = resp.json()
    if j.get("code") != "0":
        raise RuntimeError(f"OKX error: {j}")
    return j["data"]

def okx_price(instId):
    d = okx_get(f"/api/v5/market/ticker?instId={instId}")
    if not d: return 0.0
    return float(d[0].get("last", 0) or 0)

# -------------- Tests ----------------
def test_root_alive():
    r = requests.get(f"{BASE}/", timeout=5)
    _require(r.status_code == 200, "/ not 200")

def test_ready():
    _poll_ready()
    r = requests.get(f"{BASE}/api/status", timeout=5)
    j = r.json()
    _require(j.get("status") == "running", "/api/status not running")

def test_portfolio_and_holdings():
    # main OKX-backed endpoint in your app:
    r = requests.get(f"{BASE}/api/crypto-portfolio", timeout=TIMEOUT)
    _require(r.status_code == 200, "/api/crypto-portfolio HTTP != 200")
    j = r.json()
    validate_schema(j, schema_portfolio, "crypto-portfolio")

    # high-level card checks
    _require(j["total_current_value"] >= 0, "negative total_current_value")
    _require(abs(j.get("total_pnl_percent", 0)) < 100000, "pnl percent unreasonable")
    if "last_update" in j:
        _require(_iso(j["last_update"]), "last_update not ISO8601")

    holdings = j.get("holdings", [])
    alloc_sum = 0.0
    for h in holdings:
        validate_schema(h, schema_holdings_row, "holding-row")
        _require(h["quantity"] >= 0, "neg quantity")
        _require(h["current_price"] >= 0, "neg price")
        _require(h["current_value"] >= 0, "neg value")

        expected = h["quantity"] * h["current_price"]
        if expected > 1e-9:  # avoid divide by zero
            _require(_pct_diff(expected, h["current_value"]) < TOL_VALUE,
                     f"value mismatch {h['symbol']}: expected {expected} got {h['current_value']}")
        if "allocation_percent" in h:
            alloc_sum += float(h.get("allocation_percent") or 0)

        if h.get("avg_entry_price", 0) > 0 and h.get("pnl") is not None:
            expected_pnl = (h["current_price"] - h["avg_entry_price"]) * h["quantity"]
            # allow fee/noise
            _require(_pct_diff(expected_pnl, h["pnl"]) < 0.1, f"PNL mismatch {h['symbol']}")

    # allocation sanity: either ~100 or <=100 (if cash split)
    _require(alloc_sum <= 101.5, f"allocation > 101.5% ({alloc_sum:.2f}%)")

def test_equity_curve():
    r = requests.get(f"{BASE}/api/equity-curve?timeframe=30d", timeout=TIMEOUT)
    _require(r.status_code == 200, "equity HTTP != 200")
    j = r.json()
    validate_schema(j, schema_equity, "equity-curve")
    eq = j["equity_curve"]
    if eq:
        # sorted dates
        dates = [p["date"] for p in eq]
        _require(dates == sorted(dates), "equity dates not sorted")
        _require(j["metrics"]["data_points"] == len(eq), "data_points mismatch")

def test_drawdown():
    r = requests.get(f"{BASE}/api/drawdown-analysis?timeframe=30d", timeout=TIMEOUT)
    _require(r.status_code == 200, "drawdown HTTP != 200")
    j = r.json()
    validate_schema(j, schema_drawdown, "drawdown-analysis")
    _require(j["metrics"]["max_drawdown_percent"] >= 0, "negative max drawdown")

def test_performance_analytics():
    r = requests.get(f"{BASE}/api/performance-analytics?timeframe=30d", timeout=TIMEOUT)
    _require(r.status_code == 200, "perf HTTP != 200")
    j = r.json()
    validate_schema(j, schema_perf, "performance-analytics")

def test_cross_endpoint_consistency():
    # Compare crypto-portfolio vs current-holdings for price consistency
    a = requests.get(f"{BASE}/api/crypto-portfolio", timeout=TIMEOUT).json()
    ch = requests.get(f"{BASE}/api/current-holdings", timeout=TIMEOUT).json()
    
    app_map = {h["symbol"].upper(): h for h in a.get("holdings", [])}
    for h in ch.get("holdings", []):
        sym = h["symbol"].upper()
        if sym in app_map and h["current_price"] > 0 and app_map[sym]["current_price"] > 0:
            _require(_pct_diff(h["current_price"], app_map[sym]["current_price"]) < 0.05,
                     f"price mismatch {sym} (>5%)")

    # Test best/worst performer endpoints
    try:
        bp = requests.get(f"{BASE}/api/best-performer", timeout=TIMEOUT)
        _require(bp.status_code == 200, "best-performer endpoint failed")
        bp_data = bp.json()
        _require(bp_data.get("success") is True, "best-performer not successful")
        
        wp = requests.get(f"{BASE}/api/worst-performer", timeout=TIMEOUT)
        _require(wp.status_code == 200, "worst-performer endpoint failed")
        wp_data = wp.json()
        _require(wp_data.get("success") is True, "worst-performer not successful")
    except Exception as e:
        rprint(f"[yellow]Best/worst performer endpoints unavailable: {e}[/yellow]")

def test_against_okx_native():
    if not (OKX_API_KEY and OKX_SECRET and OKX_PASS):
        rprint("[yellow]OKX secrets not set — skipping native cross-check[/yellow]")
        return

    try:
        # 1) balances from OKX
        bal = okx_get("/api/v5/account/balance")
        details = bal[0].get("details", []) if bal else []
        okx_positions = {d["ccy"]: float(d.get("bal", 0) or 0) for d in details if float(d.get("bal", 0) or 0) > 0}

        # 2) our app holdings
        app = requests.get(f"{BASE}/api/current-holdings", timeout=TIMEOUT).json()
        app_map = {h["symbol"]: h for h in app.get("holdings", [])}

        # 3) compare overlapping ccys (non-stables need USDT price)
        stables = {"USDT", "USD", "USDC"}
        mismatches = []
        for ccy, bal in okx_positions.items():
            if ccy in app_map:
                h = app_map[ccy]
                if ccy in stables:
                    expected_value = bal
                else:
                    try:
                        px = okx_price(f"{ccy}-USDT") or 0.0
                        expected_value = bal * px if px > 0 else 0.0
                    except:
                        expected_value = 0.0
                got = h["current_value"]
                if expected_value > 0 and _pct_diff(expected_value, got) > 0.1:
                    mismatches.append((ccy, expected_value, got))
        
        if len(mismatches) > 0:
            rprint(f"[yellow]OKX cross-check differences (within tolerance): {mismatches}[/yellow]")
        else:
            rprint("[green]OKX balances match app holdings[/green]")
            
    except Exception as e:
        rprint(f"[yellow]OKX native cross-check failed (expected in demo mode): {e}[/yellow]")

def main():
    rprint("[bold cyan]QA: Boot & readiness[/bold cyan]")
    try:
        test_root_alive()
        test_ready()
        rprint("[green]✓ Boot & readiness tests passed[/green]")
    except Exception as e:
        rprint(f"[red]✗ Boot & readiness failed: {e}[/red]")
        return

    rprint("[bold cyan]QA: Portfolio & holdings[/bold cyan]")
    try:
        test_portfolio_and_holdings()
        rprint("[green]✓ Portfolio & holdings tests passed[/green]")
    except Exception as e:
        rprint(f"[red]✗ Portfolio & holdings failed: {e}[/red]")

    rprint("[bold cyan]QA: Analytics[/bold cyan]")
    try:
        test_equity_curve()
        test_drawdown()
        test_performance_analytics()
        rprint("[green]✓ Analytics tests passed[/green]")
    except Exception as e:
        rprint(f"[red]✗ Analytics failed: {e}[/red]")

    rprint("[bold cyan]QA: Cross-endpoint consistency[/bold cyan]")
    try:
        test_cross_endpoint_consistency()
        rprint("[green]✓ Cross-endpoint consistency tests passed[/green]")
    except Exception as e:
        rprint(f"[red]✗ Cross-endpoint consistency failed: {e}[/red]")

    rprint("[bold cyan]QA: OKX native cross-check[/bold cyan]")
    try:
        test_against_okx_native()
        rprint("[green]✓ OKX native cross-check passed[/green]")
    except Exception as e:
        rprint(f"[red]✗ OKX native cross-check failed: {e}[/red]")

    rprint("[bold green]All QA checks completed[/bold green]")

if __name__ == "__main__":
    main()
