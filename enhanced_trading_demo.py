#!/usr/bin/env python3
"""
Enhanced Trading Algorithm Demo
Demonstrates the advanced buy/sell logic with crash failsafes and peak tracking.
"""

import sys
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# Add project paths
sys.path.append('.')
sys.path.append('src')

@dataclass
class TradingState:
    """Enhanced trading state with crash protection."""
    position_qty: float = 0.0
    entry_price: float = 0.0
    peak_since_entry: float = 0.0
    equity: float = 10000.0
    trading_enabled: bool = True
    
    # Rebuy mechanism
    rebuy_armed: bool = False
    rebuy_price: float = 0.0
    rebuy_ready_at: Optional[datetime] = None
    rebuy_dynamic: bool = True
    
    # Statistics
    total_trades: int = 0
    crash_exits: int = 0
    normal_exits: int = 0
    rebuy_trades: int = 0

@dataclass 
class TradingParams:
    """Enhanced trading parameters."""
    # Basic parameters
    fee: float = 0.0025          # 0.25% trading fee
    slip: float = 0.001          # 0.1% slippage
    risk: float = 0.01           # 1% risk per trade
    sl: float = 0.02             # 2% stop loss
    tp: float = 0.04             # 4% take profit
    
    # Bollinger Bands
    bb_period: int = 20
    bb_std: float = 2.0
    
    # ATR parameters
    atr_period: int = 14
    
    # Crash protection
    crash_atr_mult: float = 3.0   # ATR multiplier for crash detection
    crash_dd_pct: float = 0.05    # 5% drawdown threshold
    crash_require_profit: bool = True
    crash_min_profit_pct: float = 0.005  # 0.5% minimum profit
    
    # Rebuy mechanism
    rebuy_cooldown_min: int = 15  # 15 minutes cooldown
    rebuy_mode: str = "confirmation"  # "confirmation" or "knife"

def bollinger_bands(price_series: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Calculate Bollinger Bands."""
    sma = price_series.rolling(window=period).mean()
    std = price_series.rolling(window=period).std()
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return upper_band, sma, lower_band

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

def simulate_market_data(length: int = 1000) -> pd.DataFrame:
    """Generate realistic cryptocurrency market data for demonstration."""
    np.random.seed(42)  # For reproducible results
    
    # Start with a base price
    base_price = 50000.0  # BTC-like price
    
    # Generate realistic price movements
    returns = np.random.normal(0.0002, 0.02, length)  # Small positive drift with volatility
    
    # Add some trend and volatility clustering
    for i in range(1, length):
        # Add momentum and mean reversion
        momentum = returns[i-1] * 0.1
        mean_reversion = -returns[i-1] * 0.05
        returns[i] += momentum + mean_reversion
        
        # Add volatility clustering
        if abs(returns[i-1]) > 0.03:  # High volatility period
            returns[i] *= 1.5
    
    # Calculate prices
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC data
    data = []
    for i, price in enumerate(prices):
        # Simulate intraday movements
        high = price * (1 + np.random.uniform(0, 0.015))
        low = price * (1 - np.random.uniform(0, 0.015))
        open_price = prices[i-1] if i > 0 else price
        close_price = price
        
        # Ensure OHLC logic is correct
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        volume = np.random.uniform(100, 1000)
        
        data.append({
            'timestamp': datetime.now() + timedelta(hours=i),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def check_crash_exit(state: TradingState, params: TradingParams, 
                    current_price: float, current_low: float, atr_value: float) -> bool:
    """Check for crash protection exit conditions."""
    if state.position_qty <= 0.0:
        return False
    
    peak = state.peak_since_entry
    entry_price = state.entry_price
    
    # Calculate drops from peak
    drop_from_peak_close = peak - current_price
    drop_from_peak_low = peak - current_low
    drop_close_pct = drop_from_peak_close / max(1e-12, peak)
    drop_low_pct = drop_from_peak_low / max(1e-12, peak)
    
    # Check if currently in profit
    breakeven_mult = 1 + 2*params.fee + 2*params.slip + params.crash_min_profit_pct
    in_profit_now = current_price >= entry_price * breakeven_mult if params.crash_require_profit else True
    
    # Crash trigger conditions
    crash_trigger = (
        max(drop_from_peak_close, drop_from_peak_low) >= params.crash_atr_mult * atr_value
        or max(drop_close_pct, drop_low_pct) >= params.crash_dd_pct
    )
    
    return in_profit_now and crash_trigger

def compute_rebuy_price(df: pd.DataFrame, current_price: float, mode: str) -> float:
    """Compute dynamic rebuy price."""
    if mode == "confirmation":
        # For confirmation mode, set rebuy price slightly above recent support
        recent_low = df['low'].tail(10).min()
        return recent_low * 1.01  # 1% above recent low
    else:  # "knife" mode
        # For knife catching, set rebuy price below current price
        return current_price * 0.975  # 2.5% below current price

def place_limit_ioc(symbol: str, side: str, qty: float, price: float) -> dict:
    """Simulate placing a limit IOC order."""
    return {
        'id': f"order_{datetime.now().strftime('%H%M%S')}",
        'symbol': symbol,
        'side': side,
        'amount': qty,
        'price': price,
        'status': 'filled'
    }

def run_enhanced_trading_demo():
    """Run the enhanced trading algorithm demonstration."""
    print("🚀 Enhanced Trading Algorithm Demo")
    print("=" * 50)
    
    # Initialize parameters and state
    params = TradingParams()
    state = TradingState()
    
    print(f"📊 Starting Equity: ${state.equity:,.2f}")
    print(f"⚡ Crash Protection: {params.crash_atr_mult}x ATR / {params.crash_dd_pct*100:.0f}% DD")
    print(f"🔄 Rebuy Mode: {params.rebuy_mode}")
    print()
    
    # Generate market data
    print("📈 Generating realistic market data...")
    df = simulate_market_data(500)
    symbol = "BTC/USDT"
    
    # Calculate technical indicators
    bb_upper, bb_middle, bb_lower = bollinger_bands(df['close'], params.bb_period, params.bb_std)
    atr_values = atr(df, params.atr_period)
    
    # Trading simulation
    trades = []
    equity_history = []
    
    for i in range(50, len(df)):  # Start after indicators are available
        current_data = df.iloc[i]
        current_price = float(current_data['close'])
        current_high = float(current_data['high'])
        current_low = float(current_data['low'])
        current_time = current_data.name
        
        bb_up = float(bb_upper.iloc[i])
        bb_lo = float(bb_lower.iloc[i])
        atr_val = float(atr_values.iloc[i])
        
        if pd.isna(bb_up) or pd.isna(bb_lo) or pd.isna(atr_val):
            continue
        
        # Update peak tracking if in position
        if state.position_qty > 0.0:
            state.peak_since_entry = max(state.peak_since_entry, current_high)
        
        # 1. CRASH FAILSAFE - Check for emergency exit
        if check_crash_exit(state, params, current_price, current_low, atr_val):
            # Execute crash exit
            fill_price = current_price * (1 - 0.001)
            qty = state.position_qty
            gross = qty * (fill_price - state.entry_price)
            fees = params.fee * (fill_price + state.entry_price) * qty
            pnl = gross - fees
            state.equity += pnl
            
            # Arm rebuy mechanism
            state.rebuy_armed = True
            state.rebuy_price = compute_rebuy_price(df.iloc[max(0, i-10):i+1], current_price, params.rebuy_mode)
            state.rebuy_ready_at = current_time + timedelta(minutes=params.rebuy_cooldown_min)
            
            trades.append({
                'time': current_time,
                'type': 'CRASH_EXIT',
                'side': 'sell',
                'price': fill_price,
                'qty': qty,
                'pnl': pnl,
                'equity': state.equity
            })
            
            state.position_qty = 0.0
            state.entry_price = 0.0
            state.peak_since_entry = 0.0
            state.crash_exits += 1
            state.total_trades += 1
            
            print(f"💥 CRASH EXIT @ ${fill_price:,.2f} | PnL: ${pnl:,.2f} | Equity: ${state.equity:,.2f}")
            continue
        
        # 2. NORMAL EXITS
        if state.position_qty > 0.0:
            stop = state.entry_price * (1 - params.sl)
            take = state.entry_price * (1 + params.tp)
            
            if current_price >= bb_up or current_price >= take or current_low <= stop:
                # Execute normal exit
                fill_price = current_price * (1 - 0.001)
                qty = state.position_qty
                gross = qty * (fill_price - state.entry_price)
                fees = params.fee * (fill_price + state.entry_price) * qty
                pnl = gross - fees
                state.equity += pnl
                
                trades.append({
                    'time': current_time,
                    'type': 'NORMAL_EXIT',
                    'side': 'sell',
                    'price': fill_price,
                    'qty': qty,
                    'pnl': pnl,
                    'equity': state.equity
                })
                
                state.position_qty = 0.0
                state.entry_price = 0.0
                state.peak_since_entry = 0.0
                state.normal_exits += 1
                state.total_trades += 1
                
                print(f"✅ NORMAL EXIT @ ${fill_price:,.2f} | PnL: ${pnl:,.2f} | Equity: ${state.equity:,.2f}")
                continue
        
        # 3. ENTRIES
        if state.trading_enabled and state.position_qty == 0.0:
            entry_signal = False
            entry_type = "ENTRY"
            
            # Update rebuy price dynamically if armed
            if state.rebuy_armed and state.rebuy_dynamic:
                state.rebuy_price = compute_rebuy_price(df.iloc[max(0, i-10):i+1], current_price, params.rebuy_mode)
            
            # Check rebuy conditions first
            if state.rebuy_armed:
                rebuy_ready = True
                if state.rebuy_ready_at and current_time < state.rebuy_ready_at:
                    rebuy_ready = False
                
                if rebuy_ready:
                    if params.rebuy_mode == "confirmation":
                        if current_price >= state.rebuy_price:
                            entry_signal = True
                            entry_type = "REBUY_CONFIRMATION"
                    else:  # "knife" mode
                        if current_price <= state.rebuy_price:
                            entry_signal = True
                            entry_type = "REBUY_KNIFE"
                    
                    if entry_signal:
                        state.rebuy_armed = False
                        state.rebuy_trades += 1
            
            # Check baseline mean-reversion entry
            elif current_price <= bb_lo:
                entry_signal = True
                entry_type = "BASELINE_ENTRY"
            
            if entry_signal:
                # Risk-based position sizing
                risk_per_unit = max(1e-12, current_price * params.sl)
                dollars = params.risk * state.equity
                qty = max(0.0, dollars / risk_per_unit)
                
                if qty > 0.0:
                    fill_price = current_price * (1 + 0.001)
                    
                    trades.append({
                        'time': current_time,
                        'type': entry_type,
                        'side': 'buy',
                        'price': fill_price,
                        'qty': qty,
                        'pnl': 0,
                        'equity': state.equity
                    })
                    
                    state.position_qty = qty
                    state.entry_price = current_price
                    state.peak_since_entry = current_price
                    state.total_trades += 1
                    
                    print(f"🟢 {entry_type} @ ${fill_price:,.2f} | Qty: {qty:.6f} | Equity: ${state.equity:,.2f}")
        
        equity_history.append(state.equity)
    
    # Results summary
    print("\n" + "=" * 50)
    print("📈 ENHANCED TRADING RESULTS")
    print("=" * 50)
    
    if trades:
        trades_df = pd.DataFrame(trades)
        
        total_pnl = trades_df[trades_df['side'] == 'sell']['pnl'].sum()
        winning_trades = len(trades_df[(trades_df['side'] == 'sell') & (trades_df['pnl'] > 0)])
        losing_trades = len(trades_df[(trades_df['side'] == 'sell') & (trades_df['pnl'] < 0)])
        
        print(f"💰 Final Equity: ${state.equity:,.2f}")
        print(f"📊 Total Return: {(state.equity/10000 - 1)*100:.2f}%")
        print(f"📈 Total PnL: ${total_pnl:,.2f}")
        print()
        print(f"🔄 Total Trades: {state.total_trades}")
        print(f"✅ Normal Exits: {state.normal_exits}")
        print(f"💥 Crash Exits: {state.crash_exits}")
        print(f"🔄 Rebuy Trades: {state.rebuy_trades}")
        print()
        print(f"🎯 Winning Trades: {winning_trades}")
        print(f"❌ Losing Trades: {losing_trades}")
        if winning_trades + losing_trades > 0:
            win_rate = winning_trades / (winning_trades + losing_trades) * 100
            print(f"📊 Win Rate: {win_rate:.1f}%")
        
        print("\n🔍 Recent Trades:")
        for trade in trades[-10:]:  # Show last 10 trades
            time_str = trade['time'].strftime('%H:%M:%S')
            pnl_str = f"PnL: ${trade['pnl']:+.2f}" if trade['pnl'] != 0 else ""
            print(f"  {time_str} | {trade['type']:<15} | {trade['side'].upper():<4} @ ${trade['price']:>8,.2f} | {pnl_str}")
    
    else:
        print("No trades executed during simulation period.")
    
    print("\n🎯 Enhanced algorithm successfully demonstrated crash protection and rebuy mechanisms!")

if __name__ == "__main__":
    run_enhanced_trading_demo()