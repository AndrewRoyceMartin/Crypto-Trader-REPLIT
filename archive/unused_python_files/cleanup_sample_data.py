#!/usr/bin/env python3
"""
Remove sample/test trade data from database to ensure only authentic OKX data is used.
"""
import os
import sqlite3


def cleanup_sample_data():
    """Remove all sample trade data from the database."""
    if not os.path.exists('trading.db'):
        print("Database not found")
        return

    conn = sqlite3.connect('trading.db')
    cursor = conn.cursor()

    # Get count before deletion
    cursor.execute('SELECT COUNT(*) FROM trades')
    before_count = cursor.fetchone()[0]

    # Delete sample trades
    cursor.execute('''
        DELETE FROM trades
        WHERE strategy = 'Enhanced Bollinger Bands'
        OR order_id LIKE '%_BUY_%'
        OR order_id LIKE '%_SELL_%'
        OR order_id LIKE 'PEPE_%'
        OR order_id LIKE 'BTC_%'
    ''')

    # Get count after deletion
    cursor.execute('SELECT COUNT(*) FROM trades')
    after_count = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    deleted_count = before_count - after_count
    print("Database cleanup complete:")
    print(f"- Before: {before_count} trades")
    print(f"- After: {after_count} trades")
    print(f"- Deleted: {deleted_count} sample trades")

    if after_count == 0:
        print("✅ Database now contains only authentic trade data")
    else:
        print(f"ℹ️  {after_count} authentic trades remain")

if __name__ == "__main__":
    cleanup_sample_data()
