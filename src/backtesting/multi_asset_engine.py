"""
Multi-asset backtesting engine for portfolio-wide strategy testing.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from ..data.manager import DataManager
from ..strategies.base import BaseStrategy
from .engine import BacktestEngine


class MultiAssetBacktestEngine:
    """Portfolio-wide backtesting engine for multiple cryptocurrencies."""
    
    def __init__(self, config, strategy: BaseStrategy):
        """
        Initialize multi-asset backtest engine.
        
        Args:
            config: Configuration object
            strategy: Trading strategy to backtest
        """
        self.config = config
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
        # Portfolio parameters
        self.initial_capital = config.get_float('backtesting', 'initial_capital', 10000)
        self.commission = config.get_float('backtesting', 'commission', 0.001)
        self.slippage = config.get_float('backtesting', 'slippage', 0.0005)
        
        # Results storage
        self.portfolio_results = {}
        self.consolidated_results = {}
        
        # Thread-safe logging
        self._log_lock = threading.Lock()
    
    def run_portfolio_backtest(self, crypto_portfolio, days: int = 30, 
                             timeframe: str = '1h', max_workers: int = 10) -> Dict:
        """
        Run backtest across entire cryptocurrency portfolio.
        
        Args:
            crypto_portfolio: CryptoPortfolio instance with holdings
            days: Number of days to backtest
            timeframe: Data timeframe
            max_workers: Maximum parallel workers
            
        Returns:
            Comprehensive portfolio backtest results
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        self.logger.info(f"Starting portfolio backtest: {days} days, {timeframe} timeframe")
        
        # Get portfolio data
        portfolio_data = crypto_portfolio.get_portfolio_data()
        symbols = list(portfolio_data.keys())
        
        # Convert crypto symbols to trading pairs (add /USDT if needed)
        trading_symbols = []
        for symbol in symbols:
            if '/' not in symbol:
                trading_symbols.append(f"{symbol}/USDT")
            else:
                trading_symbols.append(symbol)
        
        self.logger.info(f"Backtesting {len(trading_symbols)} cryptocurrencies")
        
        # Run parallel backtests
        portfolio_results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit backtest jobs
            future_to_symbol = {}
            for symbol in trading_symbols:
                try:
                    # Get initial allocation for this crypto
                    base_symbol = symbol.split('/')[0]
                    initial_value = portfolio_data.get(base_symbol, {}).get('initial_value', 100)
                    
                    future = executor.submit(
                        self._run_single_asset_backtest,
                        symbol, start_date, end_date, timeframe, initial_value
                    )
                    future_to_symbol[future] = symbol
                except Exception as e:
                    self.logger.warning(f"Failed to submit backtest for {symbol}: {e}")
            
            # Collect results
            completed_backtests = 0
            failed_backtests = 0
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result and result.get('success', False):
                        portfolio_results[symbol] = result
                        completed_backtests += 1
                        with self._log_lock:
                            self.logger.info(f"Completed backtest for {symbol}: "
                                           f"{result['total_trades']} trades, "
                                           f"{result['total_return']:.2%} return")
                    else:
                        failed_backtests += 1
                        with self._log_lock:
                            self.logger.warning(f"Backtest failed for {symbol}")
                except Exception as e:
                    failed_backtests += 1
                    with self._log_lock:
                        self.logger.error(f"Error in backtest for {symbol}: {e}")
        
        # Consolidate results
        consolidated = self._consolidate_portfolio_results(
            portfolio_results, portfolio_data, days
        )
        
        self.logger.info(f"Portfolio backtest completed: {completed_backtests} successful, "
                        f"{failed_backtests} failed")
        
        return consolidated
    
    def _run_single_asset_backtest(self, symbol: str, start_date: datetime, 
                                 end_date: datetime, timeframe: str, 
                                 initial_value: float) -> Optional[Dict]:
        """Run backtest for a single asset."""
        try:
            # Create single-asset backtest engine
            engine = BacktestEngine(self.config, self.strategy)
            engine.initial_capital = initial_value
            
            # Run the backtest
            result = engine.run_backtest(symbol, start_date, end_date, timeframe)
            result['symbol'] = symbol
            result['initial_allocation'] = initial_value
            result['success'] = True
            
            return result
            
        except Exception as e:
            with self._log_lock:
                self.logger.error(f"Single asset backtest failed for {symbol}: {e}")
            return {
                'symbol': symbol,
                'initial_allocation': initial_value,
                'success': False,
                'error': str(e)
            }
    
    def _consolidate_portfolio_results(self, portfolio_results: Dict, 
                                     portfolio_data: Dict, days: int) -> Dict:
        """Consolidate individual asset results into portfolio metrics."""
        
        total_initial_capital = 0
        total_final_value = 0
        total_trades = 0
        total_winning_trades = 0
        portfolio_pnl = 0
        
        successful_assets = []
        failed_assets = []
        asset_performances = []
        
        for symbol, result in portfolio_results.items():
            if result.get('success', False):
                successful_assets.append(symbol)
                
                initial_value = result.get('initial_allocation', 100)
                final_value = result.get('final_value', initial_value)
                asset_return = result.get('total_return', 0)
                trades = result.get('total_trades', 0)
                win_rate = result.get('win_rate', 0)
                
                total_initial_capital += initial_value
                total_final_value += final_value
                total_trades += trades
                total_winning_trades += trades * win_rate
                portfolio_pnl += (final_value - initial_value)
                
                asset_performances.append({
                    'symbol': symbol,
                    'initial_value': initial_value,
                    'final_value': final_value,
                    'return': asset_return,
                    'return_pct': asset_return * 100,
                    'trades': trades,
                    'win_rate': win_rate,
                    'pnl': final_value - initial_value
                })
            else:
                failed_assets.append(symbol)
        
        # Calculate portfolio-wide metrics
        portfolio_return = (total_final_value - total_initial_capital) / total_initial_capital if total_initial_capital > 0 else 0
        portfolio_win_rate = total_winning_trades / total_trades if total_trades > 0 else 0
        
        # Sort assets by performance
        asset_performances.sort(key=lambda x: x['return'], reverse=True)
        
        # Get top/bottom performers
        top_performers = asset_performances[:5] if asset_performances else []
        bottom_performers = asset_performances[-5:] if len(asset_performances) > 5 else []
        
        # Calculate additional metrics
        profitable_assets = len([a for a in asset_performances if a['return'] > 0])
        profitable_ratio = profitable_assets / len(asset_performances) if asset_performances else 0
        
        annualized_return = ((total_final_value / total_initial_capital) ** (365 / days) - 1) if total_initial_capital > 0 and days > 0 else 0
        
        return {
            'success': True,
            'portfolio_summary': {
                'total_assets_tested': len(portfolio_results),
                'successful_backtests': len(successful_assets),
                'failed_backtests': len(failed_assets),
                'initial_portfolio_value': total_initial_capital,
                'final_portfolio_value': total_final_value,
                'total_portfolio_return': portfolio_return,
                'total_portfolio_pnl': portfolio_pnl,
                'annualized_return': annualized_return,
                'total_trades': total_trades,
                'portfolio_win_rate': portfolio_win_rate,
                'profitable_assets': profitable_assets,
                'profitable_ratio': profitable_ratio,
                'backtest_period_days': days
            },
            'top_performers': top_performers,
            'bottom_performers': bottom_performers,
            'individual_results': portfolio_results,
            'asset_performances': asset_performances,
            'failed_assets': failed_assets,
            'timestamp': datetime.now().isoformat()
        }