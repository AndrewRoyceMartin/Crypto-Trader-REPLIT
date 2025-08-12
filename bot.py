# bot.py
# Backtest + grid search + OKX Demo paper trading
# Adds: CSV trade log, daily loss cap, heartbeat, and a tiny /health HTTP server (Replit-friendly)

import os, sys, time, math, threading, traceback, csv
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Tuple, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pandas as pd
import ccxt

SYD = "Australia/Sydney"

# ==============================
# Environment helpers
# ==============================
def env_float(key: str, default: float) -> float:
    try:
        v = os.getenv(key)
        return float(v) if v is not None and v != "" else default
    except Exception:
        return default

def env_int(key: str, default: int) -> int:
    try:
        v = os.getenv(key)
        return int(v) if v is not None and v != "" else default
    except Exception:
        return default

def env_bool(key: str, default: bool) -> bool:
    v = os.getenv(key)
    if v is None: return default
    return str(v).strip().lower() in ("1","true","t","yes","y","on")

# ==============================
# Parameters / defaults
# ==============================
@dataclass
class Params:
    timeframe: str = os.getenv("TIMEFRAME", "1h")
    lookback: int = env_int("LOOKBACK", 2000)
    band_window: int = env_int("BAND_WINDOW", 20)
    k: float = env_float("BB_K", 1.5)                  # from your optimizer
    tp: float = env_float("TP_PCT", 0.02)              # 2%
    sl: float = env_float("SL_PCT", 0.01)              # 1%
    fee: float = env_float("FEE_RATE", 0.001)          # 0.10%
    slip: float = env_float("SLIPPAGE_PCT", 0.0005)    # 5 bps
    risk: float = env_float("RISK_PER_TRADE", 0.01)    # 1% of equity
    start_equity: float = env_float("START_EQUITY", 10_000.0)
    daily_loss_cap: float = env_float("DAILY_LOSS_CAP_PCT", 0.03)  # 3% default
    symbol_okx: str = os.getenv("SYMBOL_OKX", "BTC/USDT")
    symbol_kraken: str = os.getenv("SYMBOL_KRAKEN", "BTC/AUD")

P = Params()

# ==============================
# HTTP health server (tiny)
# ==============================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        msg = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

def start_health_server():
    port = int(os.getenv("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[health] listening on :{port}")

# ==============================
# IO helpers (CSV + heartbeat)
# ==============================
TRADES_CSV = os.getenv("TRADES_CSV", "trades.csv")
HEARTBEAT_FILE = os.getenv("HEARTBEAT_FILE", "heartbeat.txt")

def append_trade_csv(row: Dict[str, object]):
    file_exists = os.path.exists(TRADES_CSV)
    with open(TRADES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ts", "symbol", "side", "qty", "price", "order_id",
            "event", "pnl", "equity_after", "notes"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def heartbeat():
    ts = pd.Timestamp.now(tz=SYD).isoformat()
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(ts)

# ==============================
# Data / indicators
# ==============================
def fetch_history(ex: ccxt.Exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    o = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if not o:
        raise RuntimeError(f"No OHLCV for {symbol} {timeframe}")
    df = pd.DataFrame(o, columns=["ts","open","high","low","close","volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(SYD)
    df = df.sort_values("ts").set_index("ts")
    return df

def bollinger(close: pd.Series, window: int, k: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ma = close.rolling(window).mean()
    sd = close.rolling(window).std(ddof=0)
    return ma, ma + k*sd, ma - k*sd

# ==============================
# Backtest
# ==============================
def backtest(df: pd.DataFrame, P: Params) -> Dict[str, float]:
    df = df.copy().dropna()
    _, up, lo = bollinger(df["close"], P.band_window, P.k)
    df["bb_up"], df["bb_lo"] = up, lo
    df["next_open"] = df["open"].shift(-1)
    df = df.dropna()

    eq, pos, entry = P.start_equity, 0.0, 0.0
    curve = []
    trades = 0

    for ts, r in df.iterrows():
        px, nxt = float(r["close"]), float(r["next_open"])

        # EXIT
        if pos > 0.0:
            stop = entry*(1 - P.sl); take = entry*(1 + P.tp)
            if px >= float(r["bb_up"]) or px >= take or float(r["low"]) <= stop:
                fill = nxt*(1 - P.slip)
                pnl  = pos*(fill - entry) - P.fee*(fill + entry)*pos
                eq  += pnl
                pos  = 0.0
                trades += 1

        # ENTRY
        if pos == 0.0 and px <= float(r["bb_lo"]):
            fill = nxt*(1 + P.slip)
            risk_per_unit = fill*P.sl
            qty = max(0.0, (P.risk*eq)/risk_per_unit)
            if qty > 0.0:
                pos, entry = qty, fill

        curve.append({"ts": ts, "equity": eq})

    curve = pd.DataFrame(curve).set_index("ts")
    ret = curve["equity"].pct_change().fillna(0)
    sharpe = (ret.mean()/ret.std()*np.sqrt(252)) if ret.std()!=0 else 0.0
    maxdd = (curve["equity"]/curve["equity"].cummax() - 1).min() if len(curve) else 0.0

    return {
        "final_equity": float(curve["equity"].iloc[-1]) if len(curve) else float(P.start_equity),
        "trades": trades,
        "Sharpe~": float(sharpe),
        "MaxDD": float(maxdd),
    }

# ==============================
# Optimizer
# ==============================
def optimize_params(df: pd.DataFrame, P: Params,
                    k_grid=(1.25, 1.5, 1.75, 2.0, 2.25),
                    tp_grid=(0.01, 0.015, 0.02, 0.025),
                    sl_grid=(0.0075, 0.01, 0.0125, 0.015),
                    min_trades: int = 8,
                    top_n: int = 15) -> List[Dict[str, float]]:
    results: List[Dict[str, float]] = []
    for k, tp, sl in product(k_grid, tp_grid, sl_grid):
        Pk = Params(**{**P.__dict__, "k": k, "tp": tp, "sl": sl})
        m = backtest(df, Pk)
        if m["trades"] >= min_trades:
            results.append({"k": k, "tp": tp, "sl": sl, **m})
    results.sort(key=lambda x: (x["final_equity"], x["Sharpe~"]), reverse=True)
    return results[:top_n]

def try_timeframes(ex: ccxt.Exchange, symbol: str, P: Params,
                   tfs=("30m","1h","2h","4h")) -> Dict[str, List[Dict[str, float]]]:
    out: Dict[str, List[Dict[str, float]]] = {}
    for tf in tfs:
        df = fetch_history(ex, symbol, tf, P.lookback)
        out[tf] = optimize_params(df, P)
    return out

# ==============================
# Exchange factory
# ==============================
def make_exchange(name: str) -> ccxt.Exchange:
    name = name.lower()
    if name == "okx":
        ex = ccxt.okx({'enableRateLimit': True})
        if env_bool("OKX_DEMO", True):
            # OKX Demo (paper)
            ex.set_sandbox_mode(True)
            ex.headers = {**(ex.headers or {}), "x-simulated-trading": "1"}
        # If API keys provided, set them (for live/paper orders)
        k = os.getenv("OKX_API_KEY"); s = os.getenv("OKX_API_SECRET"); p = os.getenv("OKX_API_PASSPHRASE")
        if k and s and p:
            ex.apiKey, ex.secret, ex.password = k, s, p
        return ex
    elif name == "kraken":
        ex = ccxt.kraken({
            'enableRateLimit': True,
            'apiKey': os.getenv("KRAKEN_API_KEY"),
            'secret': os.getenv("KRAKEN_API_SECRET"),
        })
        return ex
    else:
        raise ValueError("Supported exchanges: okx | kraken")

# ==============================
# Paper trading (OKX Demo)
# ==============================
def place_limit_ioc(ex: ccxt.Exchange, symbol: str, side: str, qty: float, price: float) -> dict:
    price = float(ex.price_to_precision(symbol, price))
    qty   = float(ex.amount_to_precision(symbol, qty))
    return ex.create_order(symbol, 'limit', side, qty, price, {'timeInForce': 'IOC'})

@dataclass
class PaperState:
    position_qty: float = 0.0
    entry_price: float = 0.0
    equity: float = P.start_equity
    day_str: str = ""
    peak_equity_today: float = P.start_equity
    trading_enabled: bool = True

def today_syd_str() -> str:
    return pd.Timestamp.now(tz=SYD).strftime("%Y-%m-%d")

def reset_daily_if_needed(state: PaperState):
    cur_day = today_syd_str()
    if state.day_str != cur_day:
        state.day_str = cur_day
        state.peak_equity_today = state.equity
        state.trading_enabled = True
        print(f"[daily] reset for {cur_day}. equity={state.equity:.2f}")

def check_daily_cap(state: PaperState, cap_pct: float):
    # Update peak equity
    if state.equity > state.peak_equity_today:
        state.peak_equity_today = state.equity
    dd = (state.equity / state.peak_equity_today) - 1.0
    if dd <= -cap_pct:
        state.trading_enabled = False
        print(f"[risk] Daily loss cap hit ({cap_pct*100:.2f}%). Pausing until next day. equity={state.equity:.2f}, peak={state.peak_equity_today:.2f}")

def live_paper_loop_okx(symbol: str, P: Params):
    ex = make_exchange("okx")
    ex.load_markets()

    state = PaperState(equity=P.start_equity, day_str=today_syd_str(), peak_equity_today=P.start_equity)
    print(f"[paper] starting OKX Demo on {symbol} | timeframe={P.timeframe} | start_equity={P.start_equity}")

    start_health_server()

    while True:
        try:
            heartbeat()
            reset_daily_if_needed(state)
            check_daily_cap(state, P.daily_loss_cap)

            df = fetch_history(ex, symbol, P.timeframe, P.lookback)
            _, up, lo = bollinger(df["close"], P.band_window, P.k)
            last = df.iloc[-1]
            px = float(last["close"])
            bb_up, bb_lo = float(up.iloc[-1]), float(lo.iloc[-1])
            ts = df.index[-1].isoformat()

            # EXIT
            if state.position_qty > 0.0:
                stop = state.entry_price*(1 - P.sl)
                take = state.entry_price*(1 + P.tp)
                if px >= bb_up or px >= take or float(last["low"]) <= stop:
                    price = px * (1 - 0.001)  # cross the spread
                    resp = place_limit_ioc(ex, symbol, 'sell', state.position_qty, price)
                    fill_price = price
                    gross = state.position_qty * (fill_price - state.entry_price)
                    fees = P.fee * (fill_price + state.entry_price) * state.position_qty
                    pnl = gross - fees
                    state.equity += pnl
                    append_trade_csv({
                        "ts": ts, "symbol": symbol, "side": "sell", "qty": f"{state.position_qty:.8f}",
                        "price": f"{fill_price:.2f}", "order_id": resp.get("id"),
                        "event": "EXIT", "pnl": f"{pnl:.2f}", "equity_after": f"{state.equity:.2f}",
                        "notes": f"bb_up={bb_up:.2f} stop={stop:.2f} take={take:.2f}"
                    })
                    print(f"[EXIT] qty={state.position_qty:.6f} @~{fill_price:.2f} pnl={pnl:.2f} eq={state.equity:.2f}")
                    state.position_qty = 0.0
                    state.entry_price = 0.0

            # ENTRY
            if state.trading_enabled and state.position_qty == 0.0 and px <= bb_lo:
                risk_per_unit = max(1e-12, px * P.sl)
                dollars = P.risk * state.equity
                qty = max(0.0, dollars / risk_per_unit)
                if qty > 0.0:
                    price = px * (1 + 0.001)
                    resp = place_limit_ioc(ex, symbol, 'buy', qty, price)
                    state.position_qty = qty
                    state.entry_price = px  # approximate
                    append_trade_csv({
                        "ts": ts, "symbol": symbol, "side": "buy", "qty": f"{qty:.8f}",
                        "price": f"{price:.2f}", "order_id": resp.get("id"),
                        "event": "ENTRY", "pnl": "", "equity_after": f"{state.equity:.2f}",
                        "notes": f"bb_lo={bb_lo:.2f}"
                    })
                    print(f"[ENTRY] qty={qty:.6f} @~{price:.2f} eq={state.equity:.2f}")

        except Exception as e:
            print("[loop] error:", e)
            print(traceback.format_exc())

        time.sleep(60)  # run once/min; bars are typically 1h

# ==============================
# CLI entrypoints
# ==============================
def run_backtest():
    EXCHANGE = os.getenv("EXCHANGE", "okx").lower()
    SYMBOL   = P.symbol_okx if EXCHANGE == "okx" else P.symbol_kraken
    ex = make_exchange(EXCHANGE)
    ex.load_markets()
    df = fetch_history(ex, SYMBOL, P.timeframe, P.lookback)
    baseline = backtest(df, P)
    print("Baseline", EXCHANGE.upper(), SYMBOL, P.timeframe, "→", baseline)

def run_optimize():
    EXCHANGE = os.getenv("EXCHANGE", "okx").lower()
    SYMBOL   = P.symbol_okx if EXCHANGE == "okx" else P.symbol_kraken
    ex = make_exchange(EXCHANGE)
    ex.load_markets()
    df = fetch_history(ex, SYMBOL, P.timeframe, P.lookback)
    top = optimize_params(df, P)
    print("\nTop params on", P.timeframe)
    if not top:
        print("No configs met min_trades threshold.")
    else:
        for r in top:
            print(r)
    multi = try_timeframes(ex, SYMBOL, P, tfs=("30m","1h","2h","4h"))
    print("\nBest per timeframe:")
    for tf, rows in multi.items():
        print(tf, rows[0] if rows else "No result")

def run_paper():
    # OKX Demo paper loop
    symbol = P.symbol_okx
    live_paper_loop_okx(symbol, P)

# ==============================
# Main
# ==============================
if __name__ == "__main__":
    # Usage:
    #   python bot.py              -> backtest
    #   python bot.py opt          -> grid search + timeframe sweep
    #   python bot.py run          -> OKX Demo paper trading (requires OKX demo keys)
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if arg == "run":
        run_paper()
    elif arg == "opt":
        run_optimize()
    else:
        run_backtest()
