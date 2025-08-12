"""
Web interface for the algorithmic trading system.
Provides a dashboard for monitoring and controlling trading operations.
"""

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
import json
import logging
from datetime import datetime, timedelta
import threading
import time
import os

from src.config import Config
from src.utils.logging import setup_logging
from src.utils.database import DatabaseManager
from src.backtesting.engine import BacktestEngine
from src.trading.paper_trader import PaperTrader
from src.trading.live_trader import LiveTrader
from src.strategies.bollinger_strategy import BollingerBandsStrategy
from src.exchanges.okx_adapter import OKXAdapter
from src.exchanges.kraken_adapter import KrakenAdapter

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'trading-system-secret-key-2024')

# Global variables for trading system components
config = None
db_manager = None
current_trader = None
trading_thread = None
trading_status = {
    'mode': 'stopped',
    'symbol': None,
    'start_time': None,
    'is_running': False
}

def initialize_system():
    """Initialize the trading system components."""
    global config, db_manager
    
    config = Config()
    setup_logging(config.get('logging', 'level', 'INFO'))
    db_manager = DatabaseManager()
    
    app.logger.info("Trading system initialized")

def start_trader_thread(mode, symbol, timeframe):
    """Start trader in a separate thread."""
    global current_trader, trading_thread, trading_status
    
    try:
        strategy = BollingerBandsStrategy(config)
        
        if mode == 'paper':
            current_trader = PaperTrader(config, strategy)
        elif mode == 'live':
            current_trader = LiveTrader(config, strategy)
        else:
            raise ValueError(f"Invalid trading mode: {mode}")
        
        # Update status
        trading_status.update({
            'mode': mode,
            'symbol': symbol,
            'start_time': datetime.now(),
            'is_running': True
        })
        
        # Start trading in thread
        trading_thread = threading.Thread(
            target=current_trader.start_trading,
            args=(symbol, timeframe),
            daemon=True
        )
        trading_thread.start()
        
        app.logger.info(f"Started {mode} trading for {symbol}")
        
    except Exception as e:
        app.logger.error(f"Failed to start trader: {str(e)}")
        trading_status['is_running'] = False
        raise

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current system status."""
    try:
        # Get portfolio data
        portfolio_data = get_portfolio_data()
        
        # Get recent trades
        recent_trades = db_manager.get_trades(mode=trading_status['mode'], start_date=datetime.now() - timedelta(days=1))
        trades_data = recent_trades.tail(10).to_dict('records') if not recent_trades.empty else []
        
        # Get positions
        positions_df = db_manager.get_positions(mode=trading_status['mode'])
        positions_data = positions_df.to_dict('records') if not positions_df.empty else []
        
        status_data = {
            'trading_status': trading_status,
            'portfolio': portfolio_data,
            'recent_trades': trades_data,
            'positions': positions_data,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        app.logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio data."""
    try:
        portfolio_data = get_portfolio_data()
        return jsonify(portfolio_data)
    except Exception as e:
        app.logger.error(f"Error getting portfolio: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_portfolio_data():
    """Get current portfolio data."""
    try:
        if current_trader and hasattr(current_trader, 'get_portfolio_value'):
            if trading_status['mode'] == 'paper':
                portfolio_value = current_trader.get_portfolio_value()
                cash = current_trader.cash
                positions_value = portfolio_value - cash
                performance = current_trader.get_performance_summary()
            else:
                # For live trading, would need to get from exchange
                portfolio_value = 10000  # Placeholder
                cash = 5000  # Placeholder
                positions_value = 5000  # Placeholder
                performance = {}
        else:
            # Default values when not trading
            initial_capital = config.get_float('backtesting', 'initial_capital', 10000)
            portfolio_value = initial_capital
            cash = initial_capital
            positions_value = 0
            performance = {}
        
        # Get historical data for chart
        portfolio_history = db_manager.get_portfolio_history(mode=trading_status['mode'], days=7)
        
        chart_data = []
        if not portfolio_history.empty:
            chart_data = [
                {
                    'timestamp': row['timestamp'].isoformat(),
                    'value': row['total_value']
                }
                for _, row in portfolio_history.iterrows()
            ]
        
        return {
            'total_value': portfolio_value,
            'cash': cash,
            'positions_value': positions_value,
            'daily_pnl': performance.get('total_return', 0) * portfolio_value if performance else 0,
            'total_return': performance.get('total_return', 0) if performance else 0,
            'chart_data': chart_data
        }
        
    except Exception as e:
        app.logger.error(f"Error getting portfolio data: {str(e)}")
        return {
            'total_value': 0,
            'cash': 0,
            'positions_value': 0,
            'daily_pnl': 0,
            'total_return': 0,
            'chart_data': []
        }

@app.route('/api/start_trading', methods=['POST'])
def start_trading():
    """Start trading operations."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'paper')
        symbol = data.get('symbol', 'BTC/USDT')
        timeframe = data.get('timeframe', '1h')
        
        if trading_status['is_running']:
            return jsonify({'error': 'Trading is already running'}), 400
        
        # Safety check for live trading
        if mode == 'live':
            confirmation = data.get('confirmation', False)
            if not confirmation:
                return jsonify({'error': 'Live trading requires explicit confirmation'}), 400
        
        # Start trader thread
        start_trader_thread(mode, symbol, timeframe)
        
        return jsonify({'success': True, 'message': f'{mode.title()} trading started for {symbol}'})
        
    except Exception as e:
        app.logger.error(f"Error starting trading: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_trading', methods=['POST'])
def stop_trading():
    """Stop trading operations."""
    try:
        global current_trader, trading_status
        
        if not trading_status['is_running']:
            return jsonify({'error': 'Trading is not running'}), 400
        
        if current_trader:
            current_trader.stop_trading()
        
        trading_status.update({
            'mode': 'stopped',
            'symbol': None,
            'start_time': None,
            'is_running': False
        })
        
        return jsonify({'success': True, 'message': 'Trading stopped'})
        
    except Exception as e:
        app.logger.error(f"Error stopping trading: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtesting."""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTC/USDT')
        days = int(data.get('days', 30))
        timeframe = data.get('timeframe', '1h')
        
        # Initialize components
        strategy = BollingerBandsStrategy(config)
        engine = BacktestEngine(config, strategy)
        
        # Set date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Run backtest
        results = engine.run_backtest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe
        )
        
        # Save results to database
        performance_data = {
            'strategy_name': 'BollingerBands',
            'symbol': symbol,
            'start_date': start_date.date(),
            'end_date': end_date.date(),
            'total_return': results.get('total_return', 0),
            'sharpe_ratio': results.get('sharpe_ratio', 0),
            'max_drawdown': results.get('max_drawdown', 0),
            'total_trades': results.get('total_trades', 0),
            'win_rate': results.get('win_rate', 0),
            'mode': 'backtest'
        }
        
        db_manager.save_strategy_performance(performance_data)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        app.logger.error(f"Error running backtest: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """Get trade history."""
    try:
        mode = request.args.get('mode', trading_status['mode'])
        symbol = request.args.get('symbol')
        days = int(request.args.get('days', 7))
        
        start_date = datetime.now() - timedelta(days=days)
        
        trades_df = db_manager.get_trades(
            symbol=symbol,
            start_date=start_date,
            mode=mode
        )
        
        trades_data = trades_df.to_dict('records') if not trades_df.empty else []
        
        return jsonify(trades_data)
        
    except Exception as e:
        app.logger.error(f"Error getting trades: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions')
def get_positions():
    """Get current positions."""
    try:
        mode = request.args.get('mode', trading_status['mode'])
        
        positions_df = db_manager.get_positions(mode=mode)
        positions_data = positions_df.to_dict('records') if not positions_df.empty else []
        
        return jsonify(positions_data)
        
    except Exception as e:
        app.logger.error(f"Error getting positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config')
def get_config():
    """Get system configuration."""
    try:
        config_data = {
            'trading': {
                'default_symbol': config.get('trading', 'default_symbol', 'BTC/USDT'),
                'default_timeframe': config.get('trading', 'default_timeframe', '1h'),
                'position_size_percent': config.get_float('trading', 'position_size_percent', 5.0),
                'max_positions': config.get_int('trading', 'max_positions', 3)
            },
            'risk': {
                'max_portfolio_risk': config.get_float('risk', 'max_portfolio_risk', 10.0),
                'max_single_position_risk': config.get_float('risk', 'max_single_position_risk', 5.0),
                'max_daily_loss': config.get_float('risk', 'max_daily_loss', 5.0)
            },
            'strategy': {
                'bb_period': config.get_int('strategy', 'bb_period', 20),
                'bb_std_dev': config.get_float('strategy', 'bb_std_dev', 2.0),
                'atr_period': config.get_int('strategy', 'atr_period', 14)
            }
        }
        
        return jsonify(config_data)
        
    except Exception as e:
        app.logger.error(f"Error getting config: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop all trading operations."""
    try:
        global current_trader, trading_status
        
        if current_trader and hasattr(current_trader, 'emergency_stop'):
            current_trader.emergency_stop()
        elif current_trader:
            current_trader.stop_trading()
        
        trading_status.update({
            'mode': 'stopped',
            'symbol': None,
            'start_time': None,
            'is_running': False
        })
        
        app.logger.critical("EMERGENCY STOP ACTIVATED")
        
        return jsonify({'success': True, 'message': 'Emergency stop activated'})
        
    except Exception as e:
        app.logger.error(f"Error in emergency stop: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    initialize_system()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to avoid threading issues
    )
