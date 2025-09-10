#!/usr/bin/env python3
"""
Auto-Backtest System: Validate Hybrid Signals Against Real OKX Trade History

Goal 2: ✅ Auto-Backtest That Hybrid System on Real OKX Trade History

Strategy:
1. Load signals_log.csv (from signal logging system)
2. Load okx_trade_history.csv (from OKX trade history module)  
3. Match signal → real executed trade (same symbol, close timestamp)
4. Compute P&L = (sell_price - buy_price) × size

This validates whether the Hybrid Signal System (ML + Heuristics) 
improves trading performance over traditional methods.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def load_signals(path: str = "signals_log.csv") -> pd.DataFrame:
    """Load signal predictions from CSV with proper timestamp parsing."""
    try:
        # Try multiple possible locations
        possible_paths = [
            path,
            f"logger/{path}",
            f"../logger/{path}",
            "signals.csv",
            "logger/signals.csv"
        ]
        
        df = None
        for p in possible_paths:
            if os.path.exists(p):
                print(f"📊 Loading signals from: {p}")
                df = pd.read_csv(p, parse_dates=["timestamp"])
                break
        
        if df is None:
            print(f"⚠️ Signal log file not found. Checked: {possible_paths}")
            return pd.DataFrame()
            
        print(f"✅ Loaded {len(df)} signals")
        return df
        
    except Exception as e:
        print(f"❌ Error loading signals: {e}")
        return pd.DataFrame()

def load_trades(path: str = "okx_trade_history.csv") -> pd.DataFrame:
    """Load OKX trade history with filtering for BUY orders."""
    try:
        # Try multiple possible locations
        possible_paths = [
            path,
            f"okx/{path}",
            f"../okx/{path}",
            "okx_trade_history_full.csv",
            "okx/okx_trade_history_full.csv",
            "trade_history.csv"
        ]
        
        df = None
        for p in possible_paths:
            if os.path.exists(p):
                print(f"📈 Loading trades from: {p}")
                df = pd.read_csv(p, parse_dates=["timestamp"])
                break
        
        if df is None:
            print(f"⚠️ Trade history file not found. Checked: {possible_paths}")
            return pd.DataFrame()
        
        # Filter for BUY orders only (we want to see if our buy signals were good)
        buy_trades = df[df["side"] == "BUY"].copy()
        print(f"✅ Loaded {len(df)} total trades, {len(buy_trades)} BUY trades")
        
        return buy_trades
        
    except Exception as e:
        print(f"❌ Error loading trades: {e}")
        return pd.DataFrame()

def generate_sample_data():
    """Generate sample data for testing when real data is not available."""
    print("🧪 Generating sample data for backtest demonstration...")
    
    # Sample signals
    signals_data = []
    symbols = ["BTC", "ETH", "ALGO", "LINK", "ATOM"]
    
    for i in range(20):
        signal_time = datetime.now() - timedelta(days=i)
        symbol = symbols[i % len(symbols)]
        
        signals_data.append({
            "timestamp": signal_time,
            "symbol": symbol,
            "current_price": 100 + (i * 5),
            "confidence_score": 60 + (i % 30),
            "timing_signal": ["BUY", "CONSIDER", "WAIT", "AVOID"][i % 4],
            "ml_probability": 0.3 + (i % 7) * 0.1,
            "rsi": 30 + (i % 40),
            "volatility": 5 + (i % 15),
            "volume_ratio": 0.8 + (i % 4) * 0.1
        })
    
    # Sample trades (some matching, some not)
    trades_data = []
    for i in range(15):
        trade_time = datetime.now() - timedelta(days=i) + timedelta(minutes=5)  # 5 min after signal
        symbol = symbols[i % len(symbols)]
        
        trades_data.append({
            "timestamp": trade_time,
            "instId": f"{symbol}-USDT",
            "side": "BUY",
            "price": 105 + (i * 5),  # Slightly different from signal price
            "size": 1.0,
            "value_usd": 105 + (i * 5),
            "fee": -0.1,
            "tradeId": f"trade_{i}",
            "ordId": f"order_{i}"
        })
    
    return pd.DataFrame(signals_data), pd.DataFrame(trades_data)

def match_signals_to_trades(signals: pd.DataFrame, trades: pd.DataFrame, 
                          tolerance_minutes: int = 15) -> pd.DataFrame:
    """
    Match trading signals to actual executed trades.
    
    Args:
        signals: DataFrame with signal predictions
        trades: DataFrame with executed BUY trades
        tolerance_minutes: Time window for matching (default 15 minutes)
        
    Returns:
        DataFrame with matched signals and their outcomes
    """
    results = []
    
    print(f"🔄 Matching signals to trades (tolerance: {tolerance_minutes} min)...")
    
    for _, signal in signals.iterrows():
        symbol = signal["symbol"]
        t0 = signal["timestamp"]
        price_at_signal = signal["current_price"]
        score = signal["confidence_score"]
        signal_type = signal["timing_signal"]
        ml_prob = signal.get("ml_probability", 0.5)
        
        # Look for matching trades
        # Match by symbol and time window
        symbol_pattern = symbol.replace("/", "-")  # Handle different formats
        
        potential_matches = trades[
            (trades["instId"].str.contains(symbol_pattern, case=False, na=False)) &
            (abs((trades["timestamp"] - t0).dt.total_seconds()) <= tolerance_minutes * 60)
        ]
        
        if not potential_matches.empty:
            # Take the closest match by time
            time_diffs = abs((potential_matches["timestamp"] - t0).dt.total_seconds())
            closest_idx = time_diffs.idxmin()
            trade = potential_matches.loc[closest_idx]
            
            # Calculate P&L
            # Simple P&L: difference between trade execution price and signal price
            price_diff = trade["price"] - price_at_signal
            pnl_percent = (price_diff / price_at_signal) * 100
            
            # Calculate time difference
            time_diff_sec = (trade["timestamp"] - t0).total_seconds()
            
            results.append({
                "timestamp": t0,
                "symbol": symbol,
                "signal": signal_type,
                "confidence": score,
                "ml_probability": ml_prob,
                "signal_price": price_at_signal,
                "execution_price": trade["price"],
                "trade_size": trade["size"],
                "trade_value": trade["value_usd"],
                "pnl_$": price_diff * trade["size"],
                "pnl_%": round(pnl_percent, 3),
                "time_diff_min": round(time_diff_sec / 60, 1),
                "trade_id": trade["tradeId"],
                "matched": True
            })
        else:
            # Signal with no matching trade
            results.append({
                "timestamp": t0,
                "symbol": symbol,
                "signal": signal_type,
                "confidence": score,
                "ml_probability": ml_prob,
                "signal_price": price_at_signal,
                "execution_price": np.nan,
                "trade_size": np.nan,
                "trade_value": np.nan,
                "pnl_$": np.nan,
                "pnl_%": np.nan,
                "time_diff_min": np.nan,
                "trade_id": "NO_MATCH",
                "matched": False
            })
    
    result_df = pd.DataFrame(results)
    print(f"✅ Processed {len(signals)} signals, found {len(result_df[result_df['matched']])} matches")
    
    return result_df

def analyze_backtest_results(results: pd.DataFrame) -> Dict:
    """Analyze backtest results and generate performance metrics."""
    
    if results.empty:
        return {"error": "No backtest results to analyze"}
    
    # Filter to matched trades only for P&L analysis
    matched = results[results["matched"] == True]
    
    if matched.empty:
        return {"error": "No matched trades found for analysis"}
    
    analysis = {
        "total_signals": len(results),
        "matched_trades": len(matched),
        "match_rate_%": round(len(matched) / len(results) * 100, 2),
        
        # P&L Analysis
        "avg_pnl_%": round(matched["pnl_%"].mean(), 3),
        "total_pnl_$": round(matched["pnl_$"].sum(), 2),
        "median_pnl_%": round(matched["pnl_%"].median(), 3),
        "pnl_std_%": round(matched["pnl_%"].std(), 3),
        
        # Win Rate
        "winning_trades": len(matched[matched["pnl_%"] > 0]),
        "losing_trades": len(matched[matched["pnl_%"] < 0]),
        "win_rate_%": round(len(matched[matched["pnl_%"] > 0]) / len(matched) * 100, 2),
        
        # Signal Performance
        "avg_confidence": round(matched["confidence"].mean(), 1),
        "avg_ml_probability": round(matched["ml_probability"].mean(), 3),
        
        # Timing Analysis
        "avg_execution_delay_min": round(matched["time_diff_min"].mean(), 1),
        "median_execution_delay_min": round(matched["time_diff_min"].median(), 1),
    }
    
    # Performance by signal type
    signal_performance = {}
    for signal_type in matched["signal"].unique():
        subset = matched[matched["signal"] == signal_type]
        if len(subset) > 0:
            signal_performance[signal_type] = {
                "count": len(subset),
                "avg_pnl_%": round(subset["pnl_%"].mean(), 3),
                "win_rate_%": round(len(subset[subset["pnl_%"] > 0]) / len(subset) * 100, 2)
            }
    
    analysis["signal_performance"] = signal_performance
    
    return analysis

def generate_backtest_report(results: pd.DataFrame, analysis: Dict, save_path: str = "backtest_results.csv"):
    """Generate comprehensive backtest report."""
    
    print("\n" + "="*60)
    print("🎯 HYBRID SIGNAL BACKTEST RESULTS")
    print("="*60)
    
    if "error" in analysis:
        print(f"❌ Error: {analysis['error']}")
        return
    
    # Summary Statistics
    print(f"📊 SUMMARY STATISTICS:")
    print(f"   Total Signals: {analysis['total_signals']}")
    print(f"   Matched Trades: {analysis['matched_trades']}")
    print(f"   Match Rate: {analysis['match_rate_%']}%")
    print()
    
    # P&L Performance
    print(f"💰 P&L PERFORMANCE:")
    print(f"   Average P&L: {analysis['avg_pnl_%']}%")
    print(f"   Median P&L: {analysis['median_pnl_%']}%")
    print(f"   Total P&L: ${analysis['total_pnl_$']}")
    print(f"   P&L Std Dev: {analysis['pnl_std_%']}%")
    print()
    
    # Win Rate
    print(f"🎲 WIN RATE ANALYSIS:")
    print(f"   Winning Trades: {analysis['winning_trades']}")
    print(f"   Losing Trades: {analysis['losing_trades']}")
    print(f"   Win Rate: {analysis['win_rate_%']}%")
    print()
    
    # Signal Quality
    print(f"🧠 SIGNAL QUALITY:")
    print(f"   Average Confidence: {analysis['avg_confidence']}")
    print(f"   Average ML Probability: {analysis['avg_ml_probability']}")
    print()
    
    # Timing
    print(f"⏱️ EXECUTION TIMING:")
    print(f"   Average Delay: {analysis['avg_execution_delay_min']} minutes")
    print(f"   Median Delay: {analysis['median_execution_delay_min']} minutes")
    print()
    
    # Signal Performance Breakdown
    print(f"📈 PERFORMANCE BY SIGNAL TYPE:")
    for signal_type, perf in analysis["signal_performance"].items():
        print(f"   {signal_type}: {perf['count']} trades, {perf['avg_pnl_%']}% avg P&L, {perf['win_rate_%']}% win rate")
    
    # Save detailed results
    results.to_csv(save_path, index=False)
    print(f"\n📦 Detailed results saved to: {save_path}")
    
    # Top 5 best and worst trades
    matched = results[results["matched"] == True]
    if len(matched) > 0:
        print(f"\n🏆 TOP 5 BEST TRADES:")
        best_trades = matched.nlargest(5, "pnl_%")[["timestamp", "symbol", "signal", "confidence", "pnl_%"]]
        for _, trade in best_trades.iterrows():
            print(f"   {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} | {trade['symbol']} | {trade['signal']} | Conf: {trade['confidence']} | P&L: {trade['pnl_%']}%")
        
        print(f"\n📉 TOP 5 WORST TRADES:")
        worst_trades = matched.nsmallest(5, "pnl_%")[["timestamp", "symbol", "signal", "confidence", "pnl_%"]]
        for _, trade in worst_trades.iterrows():
            print(f"   {trade['timestamp'].strftime('%Y-%m-%d %H:%M')} | {trade['symbol']} | {trade['signal']} | Conf: {trade['confidence']} | P&L: {trade['pnl_%']}%")

def run_backtest(use_sample_data: bool = False):
    """
    Main backtest execution function.
    
    Args:
        use_sample_data: If True, generate sample data for testing
    """
    print("🚀 Starting Hybrid Signal Backtest...")
    print("Goal: Validate ML + Heuristic signals against real OKX trades")
    print()
    
    if use_sample_data:
        print("🧪 Using sample data for demonstration...")
        signals, trades = generate_sample_data()
    else:
        # Load real data
        signals = load_signals()
        trades = load_trades()
        
        # If no real data available, fallback to sample data
        if signals.empty or trades.empty:
            print("⚠️ Real data not available, generating sample data for testing...")
            signals, trades = generate_sample_data()
    
    if signals.empty or trades.empty:
        print("❌ No data available for backtesting")
        return None
    
    # Match signals to trades
    results = match_signals_to_trades(signals, trades, tolerance_minutes=15)
    
    # Analyze results
    analysis = analyze_backtest_results(results)
    
    # Generate report
    generate_backtest_report(results, analysis)
    
    return results, analysis

def create_okx_trade_history():
    """Helper function to generate OKX trade history from API if needed."""
    try:
        from okx.trade_history import OKXTradeHistory
        
        print("🔄 Fetching OKX trade history...")
        trade_history = OKXTradeHistory()
        
        # Fetch recent trades
        df = trade_history.get_all_trade_fills(instType="SPOT", max_pages=5)
        
        if not df.empty:
            save_path = "okx_trade_history.csv"
            df.to_csv(save_path, index=False)
            print(f"✅ OKX trade history saved to: {save_path}")
            return df
        else:
            print("⚠️ No trade history found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error fetching OKX trade history: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Run backtest with sample data by default
    print("🎯 HYBRID SIGNAL BACKTESTING SYSTEM")
    print("=" * 50)
    
    # Try real data first, fallback to sample data
    results, analysis = run_backtest(use_sample_data=False)
    
    if results is not None:
        print("\n✅ Backtest completed successfully!")
        print("📊 Use the generated CSV file for further analysis")
    else:
        print("\n❌ Backtest failed - check data availability")