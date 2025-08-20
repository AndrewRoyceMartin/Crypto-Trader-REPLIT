"""
Vectorized backtesting engine.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional
from ..data.manager import DataManager
from ..strategies.base import BaseStrategy


class BacktestEngine:
    """Vectorized backtesting engine."""
    
    def __init__(self, config, strategy: BaseStrategy):
        """
        Initialize backtest engine.
        
        Args:
            config: Configuration object
            strategy: Trading strategy to backtest
        """
        self.config = config
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
        # Backtest parameters
        self.initial_capital = config.get_float('backtesting', 'initial_capital', 10000)
        self.commission = config.get_float('backtesting', 'commission', 0.001)
        self.slippage = config.get_float('backtesting', 'slippage', 0.0005)
        
        # Results storage
        self.trades = []
        self.portfolio_values = []
        self.positions = []
    
    def run_backtest(self, symbol: str, start_date: datetime, end_date: datetime, 
                    timeframe: str = '1h') -> Dict:
        """
        Run backtest for given parameters.
        
        Args:
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            timeframe: Data timeframe
            
        Returns:
            Backtest results dictionary
        """
        self.logger.info(f"Starting backtest: {symbol} from {start_date} to {end_date}")
        
        try:
            # Initialize data manager and get historical data
            from ..exchanges.okx_adapter import OKXAdapter
            exchange_config = self.config.get_exchange_config('okx')
            exchange = OKXAdapter(exchange_config)
            
            if not exchange.connect():
                raise Exception("Failed to connect to exchange for backtesting")
            
            data_manager = DataManager(exchange, cache_enabled=True)
            data = data_manager.get_historical_data(symbol, timeframe, start_date, end_date)
            
            if data.empty:
                raise Exception("No data available for backtesting")
            
            self.logger.info(f"Loaded {len(data)} data points for backtesting")
            
            # Run simulation
            results = self._simulate_trading(data, symbol)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_metrics(results)
            
            self.logger.info("Backtest completed successfully")
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            raise
    
    def _simulate_trading(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Simulate trading on historical data.
        
        Args:
            data: Historical OHLCV data
            symbol: Trading symbol
            
        Returns:
            DataFrame with simulation results
        """
        # Initialize simulation state
        cash = self.initial_capital
        position = 0.0
        position_cost = 0.0  # Initialize position cost
        portfolio_value = self.initial_capital
        
        results = []
        
        for i in range(len(data)):
            current_data = data.iloc[:i+1]  # Data up to current point
            current_price = data['close'].iloc[i]
            current_timestamp = data.index[i]
            
            # Skip if insufficient data for strategy (need enough for Bollinger Bands + RSI)
            if len(current_data) < 30:  # Reduced minimum for shorter backtests
                results.append({
                    'timestamp': current_timestamp,
                    'price': current_price,
                    'cash': cash,
                    'position': position,
                    'portfolio_value': portfolio_value,
                    'signal': 'hold',
                    'trade_pnl': 0.0
                })
                continue
            
            # Generate signals
            signals = self.strategy.generate_signals(current_data)
            
            trade_pnl = 0.0
            signal_action = 'hold'
            
            # Process signals
            for signal in signals:
                if not self.strategy.validate_signal(signal):
                    continue
                
                signal_action = signal.action
                
                # Calculate position size
                position_size = self.strategy.calculate_position_size(
                    signal, portfolio_value, current_price
                )
                
                # Execute trade
                if signal.action == 'buy' and position <= 0:
                    # Buy signal
                    trade_value = min(cash * 0.95, position_size * current_price)  # Keep 5% cash
                    shares_to_buy = trade_value / current_price
                    
                    # Apply slippage and commission
                    execution_price = current_price * (1 + self.slippage)
                    commission_cost = trade_value * self.commission
                    
                    actual_cost = shares_to_buy * execution_price + commission_cost
                    
                    if actual_cost <= cash:
                        # Close any short position first
                        if position < 0:
                            trade_pnl += abs(position) * (position_cost - execution_price)
                            position = 0
                        
                        # Open long position
                        cash -= actual_cost
                        position += shares_to_buy
                        position_cost = execution_price
                        
                        self.trades.append({
                            'timestamp': current_timestamp,
                            'action': 'buy',
                            'price': execution_price,
                            'size': shares_to_buy,
                            'commission': commission_cost
                        })
                
                elif signal.action == 'sell' and position >= 0:
                    # Sell signal
                    if position > 0:
                        # Close long position
                        execution_price = current_price * (1 - self.slippage)
                        commission_cost = position * execution_price * self.commission
                        
                        cash += position * execution_price - commission_cost
                        trade_pnl = position * (execution_price - position_cost)
                        position = 0
                        position_cost = 0.0
                        
                        self.trades.append({
                            'timestamp': current_timestamp,
                            'action': 'sell',
                            'price': execution_price,
                            'size': position,
                            'commission': commission_cost
                        })
                    
                    else:
                        # Open short position
                        shares_to_short = position_size
                        execution_price = current_price * (1 - self.slippage)
                        commission_cost = shares_to_short * execution_price * self.commission
                        
                        cash += shares_to_short * execution_price - commission_cost
                        position -= shares_to_short
                        position_cost = execution_price
                        
                        self.trades.append({
                            'timestamp': current_timestamp,
                            'action': 'sell_short',
                            'price': execution_price,
                            'size': shares_to_short,
                            'commission': commission_cost
                        })
                
                break  # Process only first valid signal
            
            # Calculate portfolio value
            if position > 0:
                portfolio_value = cash + position * current_price
            elif position < 0:
                portfolio_value = cash - abs(position) * current_price
            else:
                portfolio_value = cash
            
            results.append({
                'timestamp': current_timestamp,
                'price': current_price,
                'cash': cash,
                'position': position,
                'portfolio_value': portfolio_value,
                'signal': signal_action,
                'trade_pnl': trade_pnl
            })
        
        return pd.DataFrame(results)
    
    def _calculate_metrics(self, results: pd.DataFrame) -> Dict:
        """
        Calculate performance metrics from simulation results.
        
        Args:
            results: Simulation results DataFrame
            
        Returns:
            Dictionary of performance metrics
        """
        try:
            if results.empty:
                return {}
            
            # Basic metrics
            final_value = results['portfolio_value'].iloc[-1]
            total_return = (final_value - self.initial_capital) / self.initial_capital
            
            # Calculate daily returns
            portfolio_values = results['portfolio_value']
            daily_returns = portfolio_values.pct_change().dropna()
            
            # Risk metrics
            volatility = daily_returns.std() * np.sqrt(365 * 24)  # Annualized for hourly data
            if volatility > 0 and not np.isnan(volatility) and not np.isinf(volatility):
                sharpe_ratio = (daily_returns.mean() * 365 * 24) / volatility
                if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio):
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
            
            # Maximum drawdown
            rolling_max = portfolio_values.expanding().max()
            drawdown = (portfolio_values - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Trade analysis
            trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
            total_trades = len(trades_df)
            
            if total_trades > 0:
                # Calculate win rate
                trade_pnls = results['trade_pnl'].abs()
                winning_trades = (trade_pnls > 0).sum()
                win_rate = winning_trades / total_trades if total_trades > 0 else 0
                
                # Average trade metrics
                avg_trade_pnl = trade_pnls.mean()
                avg_win = trade_pnls[trade_pnls > 0].mean() if winning_trades > 0 else 0
                avg_loss = trade_pnls[trade_pnls < 0].mean() if (total_trades - winning_trades) > 0 else 0
            else:
                win_rate = 0
                avg_trade_pnl = 0
                avg_win = 0
                avg_loss = 0
            
            # Calmar ratio (return / max drawdown)
            if max_drawdown < 0 and not np.isnan(max_drawdown) and not np.isinf(max_drawdown):
                calmar_ratio = abs(total_return / max_drawdown)
                if np.isnan(calmar_ratio) or np.isinf(calmar_ratio):
                    calmar_ratio = 0.0
            else:
                calmar_ratio = 0.0
            
            metrics = {
                'initial_capital': self.initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'annualized_return': total_return * 365 / len(results) * 24,  # Assuming hourly data
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'calmar_ratio': calmar_ratio,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_trade_pnl': avg_trade_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': abs(avg_win / avg_loss) if avg_loss < 0 else 0.0
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")
            return {}
    
    def get_trade_history(self) -> pd.DataFrame:
        """
        Get trade history.
        
        Returns:
            DataFrame with trade history
        """
        return pd.DataFrame(self.trades)
    
    def get_portfolio_history(self) -> pd.DataFrame:
        """
        Get portfolio value history.
        
        Returns:
            DataFrame with portfolio history
        """
        return pd.DataFrame(self.portfolio_values)
