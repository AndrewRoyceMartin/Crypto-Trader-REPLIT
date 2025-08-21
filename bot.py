# -*- coding: utf-8 -*-
"""
Algorithmic Trading Bot - Live Trading Only
Supports backtesting and optimization using historical data.
Only connects to live OKX exchange - no simulation modes.
"""

import sys
import time
import os
import traceback
from dataclasses import dataclass, field
from typing import List, Tuple, Union

import ccxt
import pandas as pd
import numpy as np
import pytz

# Environment variables
SYD = pytz.timezone("Australia/Sydney")

def _getenv(var_name: str, default: str = "") -> str:
    """Safe environment variable getter."""
    return os.getenv(var_name, default)

# ==============================
# Configuration & Parameters
# ==============================
@dataclass
class Params:
    """Trading strategy parameters."""
    # OKX symbols
    symbol_okx: str = "PEPE/USDT"
    symbol_kraken: str = "PEPE/USD"
    
    # Bollinger Band parameters
    timeframe: str = "1h"
    band_window: int = 20
    k: float = 2.0
    
    # Position sizing & risk
    start_equity: float = 10000.0
    risk_per_trade: float = 0.01  # 1% risk per trade
    sl: float = 0.10  # 10% stop loss
    tp: float = 0.20  # 20% take profit
    fee: float = 0.001  # 0.1% fee
    
    # Risk management
    daily_loss_cap: float = 0.02  # 2% max daily loss
    max_scale_ins: int = 2
    min_trades_for_stat: int = 20
    
    # Backtest configuration
    lookback: int = 2000

# Global parameters
P = Params()

# ==============================
# Exchange Connection
# ==============================
def make_exchange(name: str) -> ccxt.Exchange:
    """Create exchange instance with enhanced credential handling."""
    name = name.lower()
    if name == "okx":
        api_key = _getenv("OKX_API_KEY")
        secret_key = _getenv("OKX_SECRET_KEY")
        passphrase = _getenv("OKX_PASSPHRASE")
        hostname = _getenv("OKX_HOSTNAME", "app.okx.com")
        
        if not all([api_key, secret_key, passphrase]):
            raise ValueError("OKX credentials missing. Set OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE")
        
        ex = ccxt.okx({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'hostname': hostname,  # Regional endpoint support
            'sandbox': False,  # Always use live trading
            'enableRateLimit': True,
            'timeout': 30000,
            'options': {'defaultType': 'spot'}
        })
        
        # Always use live trading mode
        ex.set_sandbox_mode(False)
        
    elif name == "kraken":
        api_key = _getenv("KRAKEN_API_KEY")
        secret_key = _getenv("KRAKEN_SECRET_KEY")
        
        if not all([api_key, secret_key]):
            raise ValueError("Kraken credentials missing. Set KRAKEN_API_KEY, KRAKEN_SECRET_KEY")
            
        ex = ccxt.kraken({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'timeout': 30000
        })
    else:
        raise ValueError(f"Unsupported exchange: {name}")
    
    return ex

# ==============================
# Market Data & Indicators
# ==============================
def fetch_history(ex: ccxt.Exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch OHLCV data from exchange."""
    ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def bollinger(close_series: pd.Series, window: int, k: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    ma = close_series.rolling(window).mean()
    std = close_series.rolling(window).std()
    upper = ma + k * std
    lower = ma - k * std
    return ma, upper, lower

# ==============================
# Backtesting
# ==============================
def backtest(df: pd.DataFrame, P: Params) -> dict:
    """Simple Bollinger Bands mean reversion backtest."""
    if len(df) < P.band_window + 1:
        return {"error": "insufficient_data", "trades": 0}
    
    close_series = df["close"] if isinstance(df["close"], pd.Series) else pd.Series(df["close"].to_numpy(), index=df.index, name="close")
    ma, upper, lower = bollinger(close_series, P.band_window, P.k)
    
    equity = P.start_equity
    position = 0.0
    entry_price = 0.0
    trades = []
    
    for i in range(P.band_window, len(df)):
        row = df.iloc[i]
        price = row['close']
        bb_upper = upper.iloc[i]
        bb_lower = lower.iloc[i]
        
        # Entry: Buy when price touches lower band
        if position == 0 and price <= bb_lower:
            risk_amount = equity * P.risk_per_trade
            position = risk_amount / price
            entry_price = price
            equity -= position * price * P.fee  # Entry fee
            
        # Exit: Sell when price touches upper band or stop/take levels
        elif position > 0:
            stop_price = entry_price * (1 - P.sl)
            take_price = entry_price * (1 + P.tp)
            
            should_exit = (price >= bb_upper or 
                          price <= stop_price or 
                          price >= take_price)
            
            if should_exit:
                pnl = position * (price - entry_price)
                fees = position * price * P.fee
                net_pnl = pnl - fees
                equity += position * price - fees
                
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': price,
                    'pnl': net_pnl,
                    'return_pct': net_pnl / (position * entry_price)
                })
                
                position = 0.0
                entry_price = 0.0
    
    if len(trades) == 0:
        return {"trades": 0, "total_return": 0.0, "win_rate": 0.0}
    
    total_pnl = sum(t['pnl'] for t in trades)
    wins = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = wins / len(trades)
    total_return = total_pnl / P.start_equity
    
    return {
        "trades": len(trades),
        "total_return": total_return,
        "win_rate": win_rate,
        "final_equity": equity
    }

# ==============================
# Optimization
# ==============================
def optimize_params(df: pd.DataFrame, base_params: Params) -> List[dict]:
    """Grid search optimization for strategy parameters."""
    results = []
    
    # Parameter ranges
    band_windows = [15, 20, 25, 30]
    k_values = [1.5, 2.0, 2.5]
    sl_values = [0.05, 0.10, 0.15]
    tp_values = [0.15, 0.20, 0.30]
    
    for window in band_windows:
        for k in k_values:
            for sl in sl_values:
                for tp in tp_values:
                    # Create test parameters
                    test_params = Params(
                        band_window=window,
                        k=k,
                        sl=sl,
                        tp=tp,
                        timeframe=base_params.timeframe,
                        symbol_okx=base_params.symbol_okx
                    )
                    
                    result = backtest(df, test_params)
                    if result.get("trades", 0) >= base_params.min_trades_for_stat:
                        result.update({
                            "window": window,
                            "k": k,
                            "sl": sl,
                            "tp": tp
                        })
                        results.append(result)
    
    # Sort by total return
    results.sort(key=lambda x: x.get("total_return", -999), reverse=True)
    return results[:10]  # Top 10 results

def try_timeframes(ex: ccxt.Exchange, symbol: str, base_params: Params, tfs: Tuple[str, ...]) -> dict:
    """Test strategy across multiple timeframes."""
    results = {}
    
    for tf in tfs:
        try:
            test_params = Params(
                timeframe=tf,
                symbol_okx=base_params.symbol_okx,
                band_window=base_params.band_window,
                k=base_params.k
            )
            
            limit = max(5 * test_params.band_window, min(test_params.lookback, 1000))
            df = fetch_history(ex, symbol, tf, limit)
            optimized = optimize_params(df, test_params)
            results[tf] = optimized
            
        except Exception as e:
            print(f"Error testing {tf}: {e}")
            results[tf] = []
    
    return results

# ==============================
# Utility Functions
# ==============================
def today_syd_str() -> str:
    """Get current date in Sydney timezone as string."""
    return pd.Timestamp.now(tz=SYD).strftime("%Y-%m-%d")

def timeframe_to_seconds(tf: str) -> int:
    """Convert timeframe string to seconds."""
    tf = tf.strip().lower()
    units = {'m': 60, 'h': 3600, 'd': 86400}
    n = int(''.join([c for c in tf if c.isdigit()]) or 1)
    u = tf[-1] if tf[-1] in units else 'h'
    return n * units[u]

# ==============================
# CLI Functions
# ==============================
def run_backtest():
    """Run backtest on historical data."""
    EXCHANGE = os.getenv("EXCHANGE", "okx").lower()
    SYMBOL = P.symbol_okx if EXCHANGE == "okx" else P.symbol_kraken
    ex = make_exchange(EXCHANGE)
    ex.load_markets()
    limit = max(5 * P.band_window, min(P.lookback, 3000))
    df = fetch_history(ex, SYMBOL, P.timeframe, limit)
    baseline = backtest(df, P)
    print("Baseline", EXCHANGE.upper(), SYMBOL, P.timeframe, "→", baseline)

def run_optimize():
    """Run parameter optimization."""
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

# ==============================
# Main
# ==============================
if __name__ == "__main__":
    # Usage:
    #   python bot_clean.py              -> backtest
    #   python bot_clean.py opt          -> grid search + timeframe sweep
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if arg == "opt":
        run_optimize()
    else:
        run_backtest()