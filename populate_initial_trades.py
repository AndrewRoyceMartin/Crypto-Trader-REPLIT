#!/usr/bin/env python3
"""
Script to populate initial $100 purchases for each cryptocurrency in the portfolio.
This creates realistic trade records and open positions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.database import DatabaseManager
from src.data.crypto_portfolio import CryptoPortfolioManager
from datetime import datetime, timedelta
import random

def populate_initial_trades():
    """Create initial $100 purchase records for each crypto."""
    
    # Initialize systems
    db_manager = DatabaseManager()
    crypto_portfolio = CryptoPortfolioManager()
    
    # Get all cryptos in portfolio
    portfolio_data = crypto_portfolio.get_portfolio_data()
    
    purchase_time = datetime.now() - timedelta(days=7)  # Simulate purchases 7 days ago
    
    print(f"Creating initial $100 purchase records for {len(portfolio_data)} cryptocurrencies...")
    
    trades_added = 0
    positions_added = 0
    
    for symbol, crypto_data in portfolio_data.items():
        try:
            # Calculate purchase details
            current_price = crypto_data['current_price']
            initial_value = crypto_data['initial_value']  # Should be $100
            quantity = crypto_data['quantity']
            
            # Calculate purchase price (what it was 7 days ago)
            pnl_percent = crypto_data.get('pnl_percent', 0)
            purchase_price = current_price / (1 + (pnl_percent / 100))
            
            # Add purchase trade record
            trade_data = {
                'timestamp': purchase_time,
                'symbol': symbol,
                'action': 'BUY',
                'size': quantity,
                'price': purchase_price,
                'commission': initial_value * 0.001,  # 0.1% commission
                'order_id': f"INIT_{symbol}_{int(purchase_time.timestamp())}",
                'strategy': 'INITIAL_INVESTMENT',
                'confidence': 1.0,
                'pnl': 0,  # No PnL at purchase
                'mode': 'paper'
            }
            
            trade_id = db_manager.save_trade(trade_data)
            trades_added += 1
            
            # Add open position
            position_data = {
                'symbol': symbol,
                'size': quantity,
                'avg_price': purchase_price,
                'entry_time': purchase_time,
                'stop_loss': purchase_price * 0.9,  # 10% stop loss
                'take_profit': purchase_price * 1.2,  # 20% take profit
                'unrealized_pnl': crypto_data['pnl'],
                'status': 'open',
                'mode': 'paper'
            }
            
            position_id = db_manager.save_position(position_data)
            positions_added += 1
            
            print(f"✅ {symbol}: ${initial_value:.2f} at ${purchase_price:.6f} - Current PnL: {pnl_percent:.2f}%")
            
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")
            continue
    
    print(f"\n🎉 Successfully created:")
    print(f"   📈 {trades_added} purchase trades")
    print(f"   💼 {positions_added} open positions")
    print(f"   💰 Total invested: ${trades_added * 100:.2f}")

if __name__ == "__main__":
    populate_initial_trades()