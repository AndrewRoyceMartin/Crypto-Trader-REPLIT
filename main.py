#!/usr/bin/env python3
"""
Main entry point for the algorithmic trading system.
Provides CLI interface for backtesting, paper trading, and live trading.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from src.config import Config
from src.utils.logging import setup_logging
from src.backtesting.engine import BacktestEngine
from src.trading.paper_trader import PaperTrader
from src.trading.live_trader import LiveTrader
from src.strategies.bollinger_strategy import BollingerBandsStrategy


def run_backtest(args):
    """Run backtesting mode."""
    config = Config()
    setup_logging(config.get('logging', 'level', fallback='INFO'))
    
    logger = logging.getLogger(__name__)
    logger.info("Starting backtest mode")
    
    try:
        # Initialize strategy
        strategy = BollingerBandsStrategy(config)
        
        # Initialize backtest engine
        engine = BacktestEngine(config, strategy)
        
        # Set date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        # Run backtest
        results = engine.run_backtest(
            symbol=args.symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe=args.timeframe
        )
        
        # Display results
        print("\n=== BACKTEST RESULTS ===")
        print(f"Symbol: {args.symbol}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Total Return: {results['total_return']:.2%}")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2%}")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate']:.2%}")
        
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}")
        sys.exit(1)


def run_paper_trading(args):
    """Run paper trading mode."""
    config = Config()
    setup_logging(config.get('logging', 'level', fallback='INFO'))
    
    logger = logging.getLogger(__name__)
    logger.info("Starting paper trading mode")
    
    try:
        # Initialize strategy
        strategy = BollingerBandsStrategy(config)
        
        # Initialize paper trader
        trader = PaperTrader(config, strategy)
        
        # Start trading
        trader.start_trading(args.symbol, args.timeframe)
        
    except KeyboardInterrupt:
        logger.info("Paper trading stopped by user")
    except Exception as e:
        logger.error(f"Paper trading failed: {str(e)}")
        sys.exit(1)


def run_live_trading(args):
    """Run live trading mode."""
    config = Config()
    setup_logging(config.get('logging', 'level', fallback='INFO'))
    
    logger = logging.getLogger(__name__)
    logger.info("Starting live trading mode")
    
    # Safety confirmation
    if not args.confirm:
        print("WARNING: This will execute real trades with real money!")
        confirm = input("Type 'YES' to confirm live trading: ")
        if confirm != 'YES':
            print("Live trading cancelled.")
            return
    
    try:
        # Initialize strategy
        strategy = BollingerBandsStrategy(config)
        
        # Initialize live trader
        trader = LiveTrader(config, strategy)
        
        # Start trading
        trader.start_trading(args.symbol, args.timeframe)
        
    except KeyboardInterrupt:
        logger.info("Live trading stopped by user")
    except Exception as e:
        logger.error(f"Live trading failed: {str(e)}")
        sys.exit(1)


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Algorithmic Trading System")
    subparsers = parser.add_subparsers(dest='mode', help='Trading modes')
    
    # Backtest mode
    backtest_parser = subparsers.add_parser('backtest', help='Run backtesting')
    backtest_parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol')
    backtest_parser.add_argument('--timeframe', default='1h', help='Timeframe')
    backtest_parser.add_argument('--days', type=int, default=30, help='Days to backtest')
    
    # Paper trading mode
    paper_parser = subparsers.add_parser('paper', help='Run paper trading')
    paper_parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol')
    paper_parser.add_argument('--timeframe', default='1h', help='Timeframe')
    
    # Live trading mode
    live_parser = subparsers.add_parser('live', help='Run live trading')
    live_parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol')
    live_parser.add_argument('--timeframe', default='1h', help='Timeframe')
    live_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # Web interface mode
    web_parser = subparsers.add_parser('web', help='Start web interface')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        run_backtest(args)
    elif args.mode == 'paper':
        run_paper_trading(args)
    elif args.mode == 'live':
        run_live_trading(args)
    elif args.mode == 'web':
        from web_interface import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
