#!/usr/bin/env python3
"""Add the available positions API endpoint to app.py"""

import re

# Read the current app.py file
with open('app.py', 'r') as f:
    content = f.read()

# API endpoint code to add
endpoint_code = '''
@app.route('/api/available-positions')
def get_available_positions():
    """Get cryptocurrencies with zero balance ready for buy-back"""
    try:
        currency = request.args.get('currency', 'USD')
        logger.info(f"Fetching available positions with currency: {currency}")
        
        # Get all trade history to find sold-out positions
        from src.utils.database import DatabaseManager
        database_manager = DatabaseManager()
        trades_df = database_manager.get_trades()
        
        if trades_df.empty:
            return jsonify({
                'success': True,
                'available_positions': [],
                'count': 0
            })
        
        # Convert DataFrame to list of dictionaries for easier processing
        trades = trades_df.to_dict('records')
        
        # Group trades by symbol to find last exit trades
        symbol_trades = {}
        for trade in trades:
            symbol = trade.get('symbol', '')
            if symbol and symbol != 'SAMPLE':  # Skip sample data
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(trade)
        
        # Get current balances from OKX
        current_balances = okx_adapter.get_balance()
        
        available_positions = []
        
        for symbol, symbol_trade_list in symbol_trades.items():
            try:
                # Sort trades by timestamp to get the most recent
                sorted_trades = sorted(symbol_trade_list, key=lambda x: x.get('timestamp', 0), reverse=True)
                
                # Check if current balance is zero or very small
                current_balance = current_balances.get(symbol, {}).get('total', 0)
                
                if current_balance == 0 or current_balance < 0.01:
                    # This is a sold-out position - find last sell trade
                    last_sell_trades = [t for t in sorted_trades if str(t.get('side', '')).upper() == 'SELL']
                    
                    if last_sell_trades:
                        last_sell = last_sell_trades[0]
                        last_exit_price = float(last_sell.get('price', 0))
                        
                        if last_exit_price > 0:
                            # Get current market price
                            try:
                                ticker = okx_adapter.exchange.fetch_ticker(f"{symbol}/USDT")
                                current_price = float(ticker['last'])
                            except:
                                current_price = last_exit_price
                            
                            # Calculate target buy price (15% below last exit)
                            target_buy_price = last_exit_price * 0.85
                            
                            # Calculate days since exit
                            last_trade_date = last_sell.get('timestamp')
                            days_since_exit = 0
                            if last_trade_date:
                                try:
                                    from datetime import datetime
                                    if isinstance(last_trade_date, str):
                                        # Handle ISO format
                                        last_date = datetime.fromisoformat(last_trade_date.replace('Z', '+00:00'))
                                    else:
                                        # Handle timestamp
                                        last_date = datetime.fromtimestamp(last_trade_date / 1000 if last_trade_date > 1e10 else last_trade_date)
                                    days_since_exit = (datetime.now() - last_date).days
                                except Exception as date_error:
                                    logger.debug(f"Error parsing date for {symbol}: {date_error}")
                                    days_since_exit = 0
                            
                            # Determine buy signal
                            buy_signal = "BUY READY" if current_price <= target_buy_price else "WAIT"
                            
                            available_positions.append({
                                'symbol': symbol,
                                'current_balance': current_balance,
                                'last_exit_price': last_exit_price,
                                'current_price': current_price,
                                'target_buy_price': target_buy_price,
                                'price_difference': current_price - target_buy_price,
                                'price_diff_percent': ((current_price - target_buy_price) / target_buy_price) * 100 if target_buy_price > 0 else 0,
                                'buy_signal': buy_signal,
                                'last_trade_date': last_trade_date,
                                'days_since_exit': days_since_exit
                            })
            except Exception as symbol_error:
                logger.debug(f"Error processing symbol {symbol}: {symbol_error}")
                continue
        
        logger.info(f"Found {len(available_positions)} available positions for buy-back")
        
        return jsonify({
            'success': True,
            'available_positions': available_positions,
            'count': len(available_positions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching available positions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
'''

# Find where to insert the endpoint - after current holdings function
pattern = r'(@app\.route\(\'/api/current-holdings\'\).*?return jsonify\(\{\'success\': False, \'error\': str\(e\)\}\), 500)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insert the new endpoint after the current holdings endpoint
    insert_pos = match.end()
    new_content = content[:insert_pos] + endpoint_code + content[insert_pos:]
    
    # Write the updated content back to app.py
    with open('app.py', 'w') as f:
        f.write(new_content)
    
    print("Successfully added available-positions API endpoint to app.py")
else:
    print("Could not find the current-holdings endpoint to insert after")