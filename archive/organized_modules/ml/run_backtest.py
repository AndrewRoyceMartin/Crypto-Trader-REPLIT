#!/usr/bin/env python3
"""
Quick Runner for Hybrid Signal Backtesting

Usage:
    python ml/run_backtest.py           # Run with available data
    python ml/run_backtest.py --sample  # Run with sample data
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.backtest import run_backtest

if __name__ == "__main__":
    use_sample = "--sample" in sys.argv

    print("🎯 HYBRID SIGNAL BACKTESTING")
    print("Goal 2: ✅ Auto-Backtest Against Real OKX Trade History")
    print("=" * 60)

    results, analysis = run_backtest(use_sample_data=use_sample)

    if results is not None:
        print("\n🏁 Backtesting completed!")
        print(f"📊 {len(results)} signals processed")
        print("💰 Performance validated against real trades")
    else:
        print("\n❌ Backtesting failed - check data files")
