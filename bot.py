# bot.py
# Backtest + grid search + OKX Demo paper trading
# Adds: CSV trade log, daily loss cap, heartbeat, tiny /health HTTP server
# Improvements: mark-to-market equity, realistic exits, dynamic Sharpe scaling, leaner OHLCV pulls,
# min-notional/amount checks, partial-fill handling for IOC, timeframe-aligned sleep,
# VWAP tracking for multi-leg positions (optional scaling-in), IOC retries with price nudging.

import os
import sys
import time
import math
import threading
import traceback
import csv
from dataclasses import dataclass, replace
from itertools import product
from typing import Dict, List, Tuple, Optional, Literal, cast
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
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "t", "yes", "y", "on")

# IOC retry tuning
IOC_RETRIES       = env_int("IOC_RETRIES", 2)            # extra attempts after first
PRICE_NUDGE_BPS   = env_float("PRICE_NUDGE_BPS", 5.0)    # per retry, bps aggressiveness (0.01% = 1bps)
CAP_FLATTEN       = env_bool("CAP_FLATTEN", False)       # flatten on daily cap hit
ALLOW_SCALE_IN    = env_bool("ALLOW_SCALE_IN", False)    # allow multi-leg adds
MAX_SCALE_INS     = env_int("MAX_SCALE_INS", 2)          # max additional entries after initial
SCALE_IN_GAP_PCT  = env_float("SCALE_IN_GAP_PCT", 0.007) # require price to be this much below last add

# ==============================
# Parameters / defaults
# ==============================
@dataclass
class Params:
    timeframe: str = os.getenv("TIMEFRAME", "1h")
    lookback: int = env_int("LOOKBACK", 2000)
    band_window: int = env_int("BAND_WINDOW", 20)
    k: float = env_float("BB_K", 1.5)
    tp: float = env_float("TP_PCT", 0.02)              # 2%
    sl: float = env_float("SL_PCT", 0.01)              # 1%
    fee: float = env_float("FEE_RATE", 0.001)          # 0.10%
    slip: float = env_float("SLIPPAGE_PCT", 0.0005)    # 5 bps
    risk: float = env_float("RISK_PER_TRADE", 0.01)    # 1% of equity
    start_equity: float = env_float("START_EQUITY", 10_000.0)
    daily_loss_cap: float = env_float("DAILY_LOSS_CAP_PCT", 0.03)  # 3%
    symbol_okx: str = os.getenv("SYMBOL_OKX", "BTC/USDT")
    symbol_kraken: str = os.getenv("SYMBOL_KRAKEN", "BTC/AUD")

P = Params()

# ==============================
# HTTP health server (tiny)
# ==============================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        msg = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

def start_health_server():
    port = int(os.getenv("BOT_HEALTH_PORT", "8001"))
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
def _df_from_ohlcv(ohlcv: List[List[float]]) -> pd.DataFrame:
    # Build then rename; avoids earlier "columns" kwarg stub confusion
    df = pd.DataFrame(ohlcv)
    if df.shape[1] >= 6:
        df = df.rename(columns={0: "ts", 1: "open", 2: "high", 3: "low", 4: "close", 5: "volume"})
        # cast to satisfy pyright that this is a DataFrame, not a Series
        return cast(pd.DataFrame, df[["ts", "open", "high", "low", "close", "volume"]])
    # Pad if fewer cols
    need = ["ts", "open", "high", "low", "close", "volume"]
    cur = list(df.columns)
    mapping = {cur[i]: need[i] for i in range(min(len(cur), 6))}
    df = df.rename(columns=mapping)
    for name in need:
        if name not in df.columns:
            df[name] = np.nan
    return cast(pd.DataFrame, df[need])

def fetch_history(ex: ccxt.Exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    o = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)  # type: ignore[no-untyped-call]
    if not o:
        raise RuntimeError(f"No OHLCV for {symbol} {timeframe}")
    df = _df_from_ohlcv(cast(List[List[float]], o))
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(SYD)
    df = df.sort_values("ts").set_index("ts")
    return df

def bollinger(close: pd.Series, window: int, k: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    # ensure close is a true Series (not a DataFrame)
    close_s = pd.Series(close.to_numpy(), index=close.index, name=getattr(close, "name", "close"))
    ma = close_s.rolling(window).mean()
    sd = close_s.rolling(window).std(ddof=0)
    up = ma + k * sd
    lo = ma - k * sd
    return cast(Tuple[pd.Series, pd.Series, pd.Series], (ma, up, lo))

def infer_bars_per_year(idx: pd.Index) -> float:
    try:
        dt_idx = pd.DatetimeIndex(idx)
    except Exception:
        return 252.0
    if len(dt_idx) < 3:
        return 252.0
    diffs_ns = np.diff(dt_idx.asi8)
    med_secs = float(np.median(diffs_ns)) / 1e9
    if med_secs <= 0:
        return 252.0
    return (365.0 * 24.0 * 3600.0) / med_secs

# ==============================
# Backtest
# ==============================
def backtest(df: pd.DataFrame, P: Params) -> Dict[str, float]:
    df = df.copy()
    # Rebuild strongly-typed Series to satisfy pyright
    close_series = pd.Series(df["close"].to_numpy(), index=df.index, name="close")
    open_series = pd.Series(df["open"].to_numpy(), index=df.index, name="open")

    ma, up, lo = bollinger(close_series, P.band_window, P.k)
    df["bb_up"], df["bb_lo"] = up, lo
    df["next_open"] = open_series.shift(-1)
    df = df.dropna(subset=["bb_up", "bb_lo", "next_open"])

    eq_cash = P.start_equity
    pos, entry = 0.0, 0.0
    curve: List[Dict[str, object]] = []
    trades = 0

    for ts, r in df.iterrows():
        px = float(r["close"])
        hi = float(r["high"])
        lw = float(r["low"])
        nxt_open = float(r["next_open"])
        bb_up = float(r["bb_up"])
        bb_lo = float(r["bb_lo"])

        # EXIT (assume intra-bar trigger: stop first if both)
        if pos > 0.0:
            stop = entry * (1 - P.sl)
            take = entry * (1 + P.tp)
            hit_stop = lw <= stop
            hit_take = (hi >= take) or (hi >= bb_up)
            fill_px: Optional[float] = None
            if hit_stop and hit_take:
                fill_px = stop * (1 - P.slip)
            elif hit_stop:
                fill_px = stop * (1 - P.slip)
            elif hit_take:
                tgt = max(take, bb_up)
                fill_px = tgt * (1 - P.slip)
            if fill_px is not None:
                gross = pos * (fill_px - entry)
                fees = P.fee * (fill_px + entry) * pos
                pnl = gross - fees
                eq_cash += pnl
                pos = 0.0
                entry = 0.0
                trades += 1

        # ENTRY
        if pos == 0.0 and (lw <= bb_lo):
            fill_px = nxt_open * (1 + P.slip)
            risk_per_unit = max(1e-12, fill_px * P.sl)
            qty = max(0.0, (P.risk * eq_cash) / risk_per_unit)
            if qty > 0.0:
                pos, entry = qty, fill_px

        # MTM equity
        eq_mtm = eq_cash + (pos * (px - entry) if pos > 0 else 0.0)
        curve.append({"ts": ts, "equity": float(eq_mtm)})

    curve_df = pd.DataFrame(curve).set_index("ts").sort_index()
    if curve_df.empty:
        return {"final_equity": float(P.start_equity), "trades": 0, "Sharpe~": 0.0, "MaxDD": 0.0}

    ret = curve_df["equity"].pct_change().fillna(0.0)
    ann_factor = infer_bars_per_year(curve_df.index)
    vol = float(ret.std())
    sharpe = float((float(ret.mean()) / vol) * math.sqrt(ann_factor)) if vol != 0 else 0.0
    maxdd = float((curve_df["equity"] / curve_df["equity"].cummax() - 1.0).min())
    return {"final_equity": float(curve_df["equity"].iloc[-1]), "trades": trades, "Sharpe~": sharpe, "MaxDD": maxdd}

# ==============================
# Optimizer
# ==============================
def optimize_params(
    df: pd.DataFrame,
    P: Params,
    k_grid=(1.25, 1.5, 1.75, 2.0, 2.25),
    tp_grid=(0.01, 0.015, 0.02, 0.025),
    sl_grid=(0.0075, 0.01, 0.0125, 0.015),
    min_trades: int = 8,
    top_n: int = 15
) -> List[Dict[str, float]]:
    results: List[Dict[str, float]] = []
    for k, tp, sl in product(k_grid, tp_grid, sl_grid):
        Pk = replace(P, k=k, tp=tp, sl=sl)
        m = backtest(df, Pk)
        if m["trades"] >= min_trades:
            results.append({"k": k, "tp": tp, "sl": sl, **m})
    results.sort(key=lambda x: (x["final_equity"], x["Sharpe~"]), reverse=True)
    return results[:top_n]

def try_timeframes(
    ex: ccxt.Exchange,
    symbol: str,
    P: Params,
    tfs=("30m", "1h", "2h", "4h")
) -> Dict[str, List[Dict[str, float]]]:
    out: Dict[str, List[Dict[str, float]]] = {}
    for tf in tfs:
        limit = max(5 * P.band_window, 200)
        df = fetch_history(ex, symbol, tf, limit)
        out[tf] = optimize_params(df, P)
    return out

# ==============================
# Exchange factory
# ==============================
def make_exchange(name: str) -> ccxt.Exchange:
    name = name.lower()
    if name == "okx":
        ex = ccxt.okx({'enableRateLimit': True})  # type: ignore[call-arg]
        if env_bool("OKX_DEMO", True):
            ex.set_sandbox_mode(True)
            ex.headers = {**(ex.headers or {}), "x-simulated-trading": "1"}
        k = os.getenv("OKX_API_KEY")
        s = os.getenv("OKX_API_SECRET")
        p = os.getenv("OKX_API_PASSPHRASE")
        if k:
            ex.apiKey = k
        if s:
            ex.secret = s
        if p:
            ex.password = p
        return ex
    elif name == "kraken":
        ex = ccxt.kraken({'enableRateLimit': True})  # type: ignore[call-arg]
        k = os.getenv("KRAKEN_API_KEY")
        s = os.getenv("KRAKEN_API_SECRET")
        if k:
            ex.apiKey = k
        if s:
            ex.secret = s
        return ex
    else:
        raise ValueError("Supported exchanges: okx | kraken")

# ==============================
# Order helpers: minimums + partial fills
# ==============================
def get_market(ex: ccxt.Exchange, symbol: str) -> dict:
    try:
        return ex.market(symbol)  # type: ignore[no-any-return]
    except Exception:
        ex.load_markets()
        return ex.market(symbol)  # type: ignore[no-any-return]

def get_minimums(
    ex: ccxt.Exchange,
    symbol: str
) -> Tuple[Optional[float], Optional[float], Optional[float], float]:
    m = get_market(ex, symbol)
    limits = m.get("limits", {}) or {}
    amt_min = (limits.get("amount", {}) or {}).get("min")
    cost_min = (limits.get("cost", {}) or {}).get("min")
    price_min = (limits.get("price", {}) or {}).get("min")
    prec = (m.get("precision", {}) or {}).get("amount", 8)
    step = 10 ** (-(int(prec) if isinstance(prec, int) else 8))
    return cast(Optional[float], amt_min), cast(Optional[float], cost_min), cast(Optional[float], price_min), float(step)

def _safe_float(x: object, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)  # type: ignore[arg-type]
    except Exception:
        return default

def adjust_qty_for_minimums(
    ex: ccxt.Exchange, symbol: str, qty: float, price: float
) -> Tuple[float, str]:
    amt_min, cost_min, _pm, step = get_minimums(ex, symbol)
    q = max(0.0, float(qty))
    note = ""
    if cost_min is not None:
        target_q = float(cost_min) / max(price, 1e-12)
        if q < target_q:
            q = target_q
            note = "bumped_to_min_cost"
    if amt_min is not None and q < float(amt_min):
        q = max(q, float(amt_min))
        note = "bumped_to_min_amount" if not note else note + "+amount"
    for _ in range(20):
        q = _safe_float(ex.amount_to_precision(symbol, q), q)
        if q <= 0:
            break
        notional = q * price
        if (cost_min is None or notional + 1e-12 >= float(cost_min)) and (amt_min is None or q + 1e-12 >= float(amt_min)):
            return q, note
        q = q + step
    return 0.0, "qty_below_min"

OrderSide = Literal["buy", "sell"]

def place_limit_ioc_and_get_fill(
    ex: ccxt.Exchange, symbol: str, side: OrderSide, qty: float, price: float
) -> dict:
    price_p = _safe_float(ex.price_to_precision(symbol, price), price)
    qty_p   = _safe_float(ex.amount_to_precision(symbol, qty), qty)
    order = ex.create_order(symbol, 'limit', side, qty_p, price_p, {'timeInForce': 'IOC'})  # type: ignore[call-arg]
    oid = order.get("id")
    try:
        time.sleep(0.25)
        if oid:
            order = ex.fetch_order(oid, symbol)
    except Exception:
        pass
    filled = _safe_float(order.get("filled"))
    avg = order.get("average")
    if avg is None:
        trades = cast(List[dict], order.get("trades") or [])
        if trades:
            fsum = 0.0
            csum = 0.0
            for t in trades:
                amt = _safe_float(t.get("amount"))
                prc = _safe_float(t.get("price"))
                cost = _safe_float(t.get("cost"), amt * prc if (amt and prc) else 0.0)
                fsum += amt
                csum += cost
            if fsum > 0:
                avg = csum / fsum
                filled = fsum
    avg_price = float(avg) if isinstance(avg, (int, float)) else (price_p if filled > 0 else 0.0)
    remaining = _safe_float(order.get("remaining"), max(0.0, qty_p - filled))
    status = str(order.get("status") or "unknown")
    return {"id": oid, "filled": filled, "avg_price": avg_price, "remaining": remaining, "status": status, "raw": order}

def ioc_with_retries(
    ex: ccxt.Exchange, symbol: str, side: OrderSide, qty: float, ref_px: float,
    retries: int = IOC_RETRIES, bps: float = PRICE_NUDGE_BPS
) -> Tuple[float, float, List[dict]]:
    """
    Tries IOC up to (1 + retries) times, nudging price each attempt.
    Returns: (total_filled_qty, vwap_price, list_of_order_summaries)
    """
    orders: List[dict] = []
    remaining = max(0.0, qty)
    filled_sum = 0.0
    cost_sum = 0.0
    for attempt in range(retries + 1):
        if remaining <= 0:
            break
        nudge = (bps / 10000.0) * attempt
        if side == "buy":
            px = ref_px * (1 + 0.001 + nudge)   # cross + nudge up
        else:
            px = ref_px * (1 - 0.001 - nudge)   # cross + nudge down
        adj_qty, note = adjust_qty_for_minimums(ex, symbol, remaining, px)
        if adj_qty <= 0:
            break
        r = place_limit_ioc_and_get_fill(ex, symbol, side, adj_qty, px)
        orders.append({**r, "note": note, "attempt": attempt})
        if r["filled"] > 0:
            filled_sum += r["filled"]
            cost_sum += r["filled"] * r["avg_price"]
            remaining = max(0.0, remaining - r["filled"])
        else:
            continue
    vwap = (cost_sum / filled_sum) if filled_sum > 0 else 0.0
    return filled_sum, vwap, orders

# ==============================
# Paper trading (OKX Demo)
# ==============================
@dataclass
class PaperState:
    position_qty: float = 0.0
    entry_price: float = 0.0    # VWAP cost basis of open position
    equity: float = P.start_equity
    day_str: str = ""
    peak_equity_today: float = P.start_equity
    trading_enabled: bool = True
    scale_ins: int = 0           # number of adds after initial entry

def today_syd_str() -> str:
    return pd.Timestamp.now(tz=SYD).strftime("%Y-%m-%d")

def reset_daily_if_needed(state: PaperState):
    cur_day = today_syd_str()
    if state.day_str != cur_day:
        state.day_str = cur_day
        state.peak_equity_today = state.equity
        state.trading_enabled = True
        state.scale_ins = 0
        print(f"[daily] reset for {cur_day}. equity={state.equity:.2f}")

def check_daily_cap(state: PaperState, cap_pct: float) -> bool:
    if state.equity > state.peak_equity_today:
        state.peak_equity_today = state.equity
    dd = (state.equity / state.peak_equity_today) - 1.0
    if dd <= -cap_pct:
        state.trading_enabled = False
        print(f"[risk] Daily loss cap hit ({cap_pct*100:.2f}%). Pausing. equity={state.equity:.2f}, peak={state.peak_equity_today:.2f}")
        return True
    return False

def timeframe_to_seconds(tf: str) -> int:
    tf = tf.strip().lower()
    units = {'m': 60, 'h': 3600, 'd': 86400}
    n = int(''.join([c for c in tf if c.isdigit()]) or 1)
    u = tf[-1]
    return n * units.get(u, 3600)

def realize_pnl_on_sell(state: PaperState, filled: float, avg_px: float, P: Params) -> float:
    if filled <= 0:
        return 0.0
    gross = filled * (avg_px - state.entry_price)
    fees = P.fee * (avg_px + state.entry_price) * filled
    pnl = gross - fees
    state.equity += pnl
    state.position_qty = max(0.0, state.position_qty - filled)
    if state.position_qty == 0.0:
        state.entry_price = 0.0
    return pnl

def update_vwap_on_buy(state: PaperState, add_qty: float, avg_px: float):
    if add_qty <= 0:
        return
    if state.position_qty <= 0:
        state.position_qty = add_qty
        state.entry_price = avg_px
    else:
        new_qty = state.position_qty + add_qty
        state.entry_price = (state.entry_price * state.position_qty + avg_px * add_qty) / new_qty
        state.position_qty = new_qty

def live_paper_loop_okx(symbol: str, P: Params):
    ex = make_exchange("okx")
    ex.load_markets()

    live_limit = max(5 * P.band_window, 200)
    state = PaperState(equity=P.start_equity, day_str=today_syd_str(), peak_equity_today=P.start_equity)
    print(f"[paper] starting OKX Demo on {symbol} | timeframe={P.timeframe} | start_equity={P.start_equity}")

    start_health_server()
    sleep_s = max(30, timeframe_to_seconds(P.timeframe) // 2)

    while True:
        try:
            heartbeat()
            reset_daily_if_needed(state)
            cap_hit = check_daily_cap(state, P.daily_loss_cap)

            df = fetch_history(ex, symbol, P.timeframe, live_limit)

            # build strict Series for calculations
            close_series = pd.Series(df["close"].to_numpy(), index=df.index, name="close")
            ma, up, lo = bollinger(close_series, P.band_window, P.k)

            last = df.iloc[-1]
            px = float(last["close"])
            hi = float(last["high"])
            lw = float(last["low"])
            bb_up, bb_lo = float(up.iloc[-1]), float(lo.iloc[-1])
            ts = str(df.index[-1])  # avoid .isoformat() typing issue

            # Optional: flatten if daily cap hit
            if cap_hit and CAP_FLATTEN and state.position_qty > 0.0:
                filled, vwap, orders = ioc_with_retries(ex, symbol, 'sell', state.position_qty, px)
                if filled > 0:
                    pnl = realize_pnl_on_sell(state, filled, vwap, P)
                    append_trade_csv({
                        "ts": ts, "symbol": symbol, "side": "sell", "qty": f"{filled:.8f}",
                        "price": f"{vwap:.2f}", "order_id": orders[-1]["id"] if orders else "",
                        "event": "CAP_FLATTEN", "pnl": f"{pnl:.2f}", "equity_after": f"{state.equity:.2f}",
                        "notes": f"retries={len(orders)-1}"
                    })
                    print(f"[FLAT] filled={filled:.6f} @~{vwap:.2f} pnl={pnl:.2f} eq={state.equity:.2f}")
                else:
                    append_trade_csv({
                        "ts": ts, "symbol": symbol, "side": "sell", "qty": f"{state.position_qty:.8f}",
                        "price": f"{px:.2f}", "order_id": "", "event": "NOFILL",
                        "pnl": "", "equity_after": f"{state.equity:.2f}", "notes": "cap_flatten"
                    })

            # EXIT (stop/take/band)
            if state.position_qty > 0.0:
                stop = state.entry_price * (1 - P.sl)
                take = state.entry_price * (1 + P.tp)
                hit_stop = lw <= stop
                hit_take = (hi >= take) or (hi >= bb_up)
                if hit_stop or hit_take:
                    filled, vwap, orders = ioc_with_retries(ex, symbol, 'sell', state.position_qty, px)
                    if filled > 0:
                        pnl = realize_pnl_on_sell(state, filled, vwap, P)
                        append_trade_csv({
                            "ts": ts, "symbol": symbol, "side": "sell", "qty": f"{filled:.8f}",
                            "price": f"{vwap:.2f}", "order_id": orders[-1]["id"] if orders else "",
                            "event": "EXIT", "pnl": f"{pnl:.2f}", "equity_after": f"{state.equity:.2f}",
                            "notes": f"bb_up={bb_up:.2f} stop={stop:.2f} take={take:.2f} retries={len(orders)-1}"
                        })
                        print(f"[EXIT] filled={filled:.6f} @~{vwap:.2f} pnl={pnl:.2f} eq={state.equity:.2f}")
                    else:
                        append_trade_csv({
                            "ts": ts, "symbol": symbol, "side": "sell", "qty": f"{state.position_qty:.8f}",
                            "price": f"{px:.2f}", "order_id": "", "event": "NOFILL",
                            "pnl": "", "equity_after": f"{state.equity:.2f}", "notes": "exit_nofill"
                        })

            # ENTRY or SCALE-IN
            can_enter = (lw <= bb_lo) and state.trading_enabled and not cap_hit
            if can_enter:
                is_scale_in = (state.position_qty > 0.0 and ALLOW_SCALE_IN and state.scale_ins < MAX_SCALE_INS)
                gap_ok = (px <= state.entry_price * (1 - SCALE_IN_GAP_PCT)) if is_scale_in else True
                if (state.position_qty == 0.0) or (is_scale_in and gap_ok):
                    risk_per_unit = max(1e-12, px * P.sl)
                    dollars = P.risk * state.equity
                    raw_qty = max(0.0, dollars / risk_per_unit)
                    if raw_qty > 0:
                        filled, vwap, orders = ioc_with_retries(ex, symbol, 'buy', raw_qty, px)
                        if filled > 0:
                            update_vwap_on_buy(state, filled, vwap)
                            if is_scale_in:
                                state.scale_ins += 1
                            append_trade_csv({
                                "ts": ts, "symbol": symbol, "side": "buy", "qty": f"{filled:.8f}",
                                "price": f"{vwap:.2f}", "order_id": orders[-1]["id"] if orders else "",
                                "event": "ENTRY" if state.scale_ins == 0 else "ADD",
                                "pnl": "", "equity_after": f"{state.equity:.2f}",
                                "notes": f"bb_lo={bb_lo:.2f} retries={len(orders)-1} scale_ins={state.scale_ins}"
                            })
                            tag = "ENTRY" if state.scale_ins == 0 else f"ADD#{state.scale_ins}"
                            print(f"[{tag}] filled={filled:.6f} @~{vwap:.2f} pos={state.position_qty:.6f} vwap={state.entry_price:.2f}")
                        else:
                            append_trade_csv({
                                "ts": ts, "symbol": symbol, "side": "buy", "qty": f"{raw_qty:.8f}",
                                "price": f"{px:.2f}", "order_id": "", "event": "NOFILL",
                                "pnl": "", "equity_after": f"{state.equity:.2f}", "notes": "entry_nofill"
                            })
                            print(f"[ENTRY] no fill (req {raw_qty:.6f})")

        except Exception as e:
            print("[loop] error:", e)
            print(traceback.format_exc())

        time.sleep(sleep_s)

# ==============================
# CLI entrypoints
# ==============================
def run_backtest():
    EXCHANGE = os.getenv("EXCHANGE", "okx").lower()
    SYMBOL = P.symbol_okx if EXCHANGE == "okx" else P.symbol_kraken
    ex = make_exchange(EXCHANGE)
    ex.load_markets()
    limit = max(5 * P.band_window, min(P.lookback, 3000))
    df = fetch_history(ex, SYMBOL, P.timeframe, limit)
    baseline = backtest(df, P)
    print("Baseline", EXCHANGE.upper(), SYMBOL, P.timeframe, "→", baseline)

def run_optimize():
    EXCHANGE = os.getenv("EXCHANGE", "okx").lower()
    SYMBOL = P.symbol_okx if EXCHANGE == "okx" else P.symbol_kraken
    ex = make_exchange(EXCHANGE)
    ex.load_markets()
    limit = max(5 * P.band_window, min(P.lookback, 3000))
    df = fetch_history(ex, SYMBOL, P.timeframe, limit)
    top = optimize_params(df, P)
    print("\nTop params on", P.timeframe)
    if not top:
        print("No configs met min_trades threshold.")
    else:
        for r in top:
            print(r)
    multi = try_timeframes(ex, SYMBOL, P, tfs=("30m", "1h", "2h", "4h"))
    print("\nBest per timeframe:")
    for tf, rows in multi.items():
        print(tf, rows[0] if rows else "No result")

def run_paper():
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
