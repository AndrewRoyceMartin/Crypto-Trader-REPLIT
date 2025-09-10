#!/usr/bin/env python3
"""
Test script to verify the $100 rebuy mechanism limit works correctly.
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from src.config import Config
from src.strategies.enhanced_bollinger_strategy import EnhancedBollingerBandsStrategy

def test_rebuy_limit():
    """Test that rebuy trades are limited to $100 maximum."""
    print("Testing Rebuy Mechanism with $100 limit...")
    
    # Create a simple config object that mimics the interface
    class MockConfig:
        def get_int(self, section, key, default=None):
            defaults = {
                ('strategy', 'bb_period'): 20,
                ('strategy', 'atr_period'): 14,
                ('strategy', 'rebuy_cooldown_min'): 15,
                ('strategy', 'fast_lookback_min'): 5,
                ('strategy', 'fast_low_window_min'): 5,
            }
            return defaults.get((section, key), default)
        
        def get_float(self, section, key, default=None):
            defaults = {
                ('trading', 'position_size_percent'): 5.0,
                ('trading', 'stop_loss_percent'): 2.0,
                ('trading', 'take_profit_percent'): 4.0,
                ('strategy', 'bb_std_dev'): 2.0,
                ('strategy', 'crash_atr_mult'): 3.0,
                ('strategy', 'crash_dd_pct'): 0.05,
                ('strategy', 'crash_min_profit_pct'): 0.005,
                ('strategy', 'rebuy_max_usd'): 100.0,
                ('trading', 'fee'): 0.0025,
                ('trading', 'slip'): 0.001,
            }
            return defaults.get((section, key), default)
        
        def get_bool(self, section, key, default=None):
            defaults = {
                ('strategy', 'rebuy_dynamic'): True,
                ('strategy', 'crash_require_profit'): True,
                ('strategy', 'fast_failsafe'): True,
            }
            return defaults.get((section, key), default)
        
        def get_str(self, section, key, default=None):
            defaults = {
                ('strategy', 'fast_tf'): '1m',
                ('strategy', 'rebuy_mode'): 'confirmation',
            }
            return defaults.get((section, key), default)
    
    config = MockConfig()
    
    # Initialize strategy
    strategy = EnhancedBollingerBandsStrategy(config)
    
    # Set up position state with high equity to test limit
    strategy.position_state['equity'] = 50000.0  # $50,000 portfolio
    strategy.position_state['rebuy_armed'] = True
    strategy.position_state['rebuy_price'] = 100.0
    strategy.position_state['rebuy_ready_at'] = datetime.now()
    
    # Create test price data
    test_price = 105.0  # Price above rebuy level (confirmation mode)
    test_atr = 2.0
    
    print(f"Portfolio equity: ${strategy.position_state['equity']:,.2f}")
    print(f"Normal position size would be: {strategy.position_size_percent}% = ${strategy.position_size_percent/100 * strategy.position_state['equity']:,.2f}")
    print(f"Rebuy max limit: ${strategy.rebuy_max_usd:.2f}")
    
    # Test rebuy signal creation
    print("\nTesting REBUY signal creation...")
    rebuy_signal = strategy._create_entry_signal(test_price, test_atr, 'REBUY_CONFIRMATION')
    
    if rebuy_signal:
        trade_value = rebuy_signal.size * rebuy_signal.price
        print(f"✓ Rebuy signal created:")
        print(f"  - Price: ${rebuy_signal.price:.2f}")
        print(f"  - Quantity: {rebuy_signal.size:.6f}")
        print(f"  - Trade value: ${trade_value:.2f}")
        print(f"  - Limited: {rebuy_signal.metadata.get('rebuy_limited', False)}")
        
        if trade_value <= strategy.rebuy_max_usd + 1:  # Allow small rounding
            print(f"✓ PASS: Rebuy trade value ${trade_value:.2f} is within limit ${strategy.rebuy_max_usd:.2f}")
        else:
            print(f"✗ FAIL: Rebuy trade value ${trade_value:.2f} exceeds limit ${strategy.rebuy_max_usd:.2f}")
            return False
    else:
        print("✗ FAIL: No rebuy signal created")
        return False
    
    # Test normal entry signal for comparison
    print("\nTesting normal BASELINE signal creation...")
    strategy.position_state['rebuy_armed'] = False  # Disable rebuy
    normal_signal = strategy._create_entry_signal(test_price, test_atr, 'BASELINE_ENTRY')
    
    if normal_signal:
        normal_trade_value = normal_signal.size * normal_signal.price
        print(f"✓ Normal signal created:")
        print(f"  - Price: ${normal_signal.price:.2f}")
        print(f"  - Quantity: {normal_signal.size:.6f}")
        print(f"  - Trade value: ${normal_trade_value:.2f}")
        
        if normal_trade_value > strategy.rebuy_max_usd:
            print(f"✓ PASS: Normal trade ${normal_trade_value:.2f} > rebuy limit ${strategy.rebuy_max_usd:.2f} (as expected)")
        else:
            print(f"⚠ WARNING: Normal trade ${normal_trade_value:.2f} <= rebuy limit ${strategy.rebuy_max_usd:.2f}")
    
    print("\n" + "="*60)
    print("✓ Rebuy mechanism with $100 limit implemented successfully!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_rebuy_limit()
    sys.exit(0 if success else 1)