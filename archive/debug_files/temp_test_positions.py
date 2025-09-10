#!/usr/bin/env python3
"""
Test script to create a comprehensive positions endpoint that includes sold/empty positions
"""
import json
from datetime import datetime

from src.services.portfolio_service import PortfolioService
from src.utils.database import DatabaseManager


def get_all_positions_including_sold():
    """Get all positions including those that have been sold/reduced to zero"""
    try:
        # Get current holdings from portfolio service
        portfolio_service = PortfolioService()
        current_holdings = portfolio_service.get_portfolio_data().get('holdings', [])

        # Get historical trades from database to find sold positions
        db = DatabaseManager()

        # Get all unique symbols that have been traded
        query = """
        SELECT DISTINCT symbol
        FROM trades
        WHERE timestamp >= datetime('now', '-30 days')
        ORDER BY symbol
        """
        traded_symbols = [row[0] for row in db.execute_query(query)]

        # Create a comprehensive positions map
        all_positions = {}

        # First, add current holdings
        for holding in current_holdings:
            symbol = holding.get('symbol')
            if symbol:
                all_positions[symbol] = {
                    'symbol': symbol,
                    'quantity': holding.get('quantity', 0),
                    'current_value': holding.get('current_value', 0),
                    'current_price': holding.get('current_price', 0),
                    'allocation_percent': holding.get('allocation_percent', 0),
                    'pnl': holding.get('pnl', 0),
                    'pnl_percent': holding.get('pnl_percent', 0),
                    'status': 'active' if holding.get('quantity', 0) > 0 else 'empty',
                    'last_trade_date': None,
                    'total_bought': 0,
                    'total_sold': 0,
                    'net_quantity': holding.get('quantity', 0)
                }

        # Then add historical positions that might be sold out
        for symbol in traded_symbols:
            if symbol not in all_positions:
                # This symbol was traded but not in current holdings - likely sold out
                all_positions[symbol] = {
                    'symbol': symbol,
                    'quantity': 0,
                    'current_value': 0,
                    'current_price': 0,
                    'allocation_percent': 0,
                    'pnl': 0,
                    'pnl_percent': 0,
                    'status': 'sold_out',
                    'last_trade_date': None,
                    'total_bought': 0,
                    'total_sold': 0,
                    'net_quantity': 0
                }

        # Calculate trade statistics for each position
        for symbol in all_positions:
            # Get trade summary for this symbol
            trade_query = """
            SELECT
                side,
                SUM(quantity) as total_quantity,
                MAX(timestamp) as last_trade
            FROM trades
            WHERE symbol = ? AND timestamp >= datetime('now', '-30 days')
            GROUP BY side
            """
            trade_data = db.execute_query(trade_query, (symbol,))

            total_bought = 0
            total_sold = 0
            last_trade_date = None

            for row in trade_data:
                side, quantity, trade_timestamp = row
                if side == 'BUY':
                    total_bought += quantity
                elif side == 'SELL':
                    total_sold += quantity

                if trade_timestamp:
                    if not last_trade_date or trade_timestamp > last_trade_date:
                        last_trade_date = trade_timestamp

            all_positions[symbol]['total_bought'] = total_bought
            all_positions[symbol]['total_sold'] = total_sold
            all_positions[symbol]['net_quantity'] = total_bought - total_sold
            all_positions[symbol]['last_trade_date'] = last_trade_date

            # Update status based on trade history
            if total_sold > 0 and abs(all_positions[symbol]['quantity']) < 0.00001:
                all_positions[symbol]['status'] = 'sold_out'
            elif total_bought > 0 and all_positions[symbol]['quantity'] > 0:
                all_positions[symbol]['status'] = 'active'
            elif total_bought > 0:
                all_positions[symbol]['status'] = 'reduced'

        return {
            'success': True,
            'positions': list(all_positions.values()),
            'total_positions': len(all_positions),
            'active_positions': len([p for p in all_positions.values() if p['status'] == 'active']),
            'sold_positions': len([p for p in all_positions.values() if p['status'] == 'sold_out']),
            'reduced_positions': len([p for p in all_positions.values() if p['status'] == 'reduced']),
            'last_update': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'positions': []
        }

if __name__ == "__main__":
    result = get_all_positions_including_sold()
    print(json.dumps(result, indent=2))
