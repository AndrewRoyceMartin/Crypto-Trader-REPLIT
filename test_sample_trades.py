#!/usr/bin/env python3
"""
Add sample trades to the database to test timeframe filtering functionality.
"""
import sqlite3
from datetime import datetime, timedelta
import json

def add_sample_trades():
    """Add realistic sample trades to the database for testing."""
    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()
    
    # Create trades table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            size REAL NOT NULL,
            price REAL NOT NULL,
            timestamp TEXT NOT NULL,
            pnl REAL DEFAULT 0,
            strategy TEXT DEFAULT '',
            order_id TEXT DEFAULT '',
            mode TEXT DEFAULT 'live'
        )
    ''')
    
    # Sample trades for the past 7 days
    now = datetime.now()
    
    sample_trades = [
        # Trade 1: PEPE buy yesterday
        {
            'symbol': 'PEPE/USDT',
            'action': 'BUY',
            'size': 1000000.0,
            'price': 0.00000845,
            'timestamp': (now - timedelta(days=1)).isoformat(),
            'pnl': 0,
            'strategy': 'Enhanced Bollinger Bands',
            'order_id': 'PEPE_BUY_001',
            'mode': 'live'
        },
        # Trade 2: BTC buy 3 days ago
        {
            'symbol': 'BTC/USDT',
            'action': 'BUY',
            'size': 0.0001,
            'price': 112500.0,
            'timestamp': (now - timedelta(days=3)).isoformat(),
            'pnl': 0,
            'strategy': 'Enhanced Bollinger Bands',
            'order_id': 'BTC_BUY_001',
            'mode': 'live'
        },
        # Trade 3: PEPE sell (partial) 2 days ago
        {
            'symbol': 'PEPE/USDT',
            'action': 'SELL',
            'size': 500000.0,
            'price': 0.00000920,
            'timestamp': (now - timedelta(days=2)).isoformat(),
            'pnl': 37.5,
            'strategy': 'Enhanced Bollinger Bands',
            'order_id': 'PEPE_SELL_001',
            'mode': 'live'
        },
        # Trade 4: Old trade (10 days ago) - should be filtered out in 7d view
        {
            'symbol': 'PEPE/USDT',
            'action': 'BUY',
            'size': 2000000.0,
            'price': 0.00000780,
            'timestamp': (now - timedelta(days=10)).isoformat(),
            'pnl': 0,
            'strategy': 'Enhanced Bollinger Bands',
            'order_id': 'PEPE_BUY_OLD',
            'mode': 'live'
        },
        # Trade 5: Recent trade (6 hours ago)
        {
            'symbol': 'BTC/USDT',
            'action': 'SELL',
            'size': 0.00005,
            'price': 114200.0,
            'timestamp': (now - timedelta(hours=6)).isoformat(),
            'pnl': 85.0,
            'strategy': 'Enhanced Bollinger Bands',
            'order_id': 'BTC_SELL_001',
            'mode': 'live'
        }
    ]
    
    # Insert trades
    for trade in sample_trades:
        cursor.execute('''
            INSERT INTO trades (symbol, action, size, price, timestamp, pnl, strategy, order_id, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade['symbol'],
            trade['action'],
            trade['size'],
            trade['price'],
            trade['timestamp'],
            trade['pnl'],
            trade['strategy'],
            trade['order_id'],
            trade['mode']
        ))
    
    conn.commit()
    
    # Verify trades were added
    cursor.execute('SELECT COUNT(*) FROM trades')
    total_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM trades WHERE timestamp > ?', 
                  [(now - timedelta(days=7)).isoformat()])
    recent_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Sample trades added successfully!")
    print(f"Total trades in database: {total_count}")
    print(f"Trades in last 7 days: {recent_count}")
    
    # Show sample of added trades
    print("\nRecent trades added:")
    for i, trade in enumerate(sample_trades[:3], 1):
        print(f"{i}. {trade['action']} {trade['size']} {trade['symbol']} @ ${trade['price']} - {trade['timestamp'][:19]}")

if __name__ == "__main__":
    add_sample_trades()