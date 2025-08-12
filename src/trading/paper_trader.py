"""
Paper trading implementation.
Simulates trading without real money.
"""

import pandas as pd
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List
from ..data.manager import DataManager
from ..strategies.base import BaseStrategy
from ..risk.manager import RiskManager
from ..exchanges.okx_adapter import OKXAdapter


class PaperTrader:
    """Paper trading simulation class."""
    
    def __init__(self, config, strategy: BaseStrategy):
        """
        Initialize paper trader.
        
        Args:
            config: Configuration object
            strategy: Trading strategy
        """
        self.config = config
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
        # Initialize exchange and data manager
        exchange_config = config.get_exchange_config('okx_demo')
        self.exchange = OKXAdapter(exchange_config)
        self.data_manager = DataManager(self.exchange, cache_enabled=True)
        
        # Initialize risk manager
        self.risk_manager = RiskManager(config)
        
        # Paper trading state
        self.initial_capital = config.get_float('backtesting', 'initial_capital', 10000)
        self.cash = self.initial_capital
        self.positions = {}
        self.orders = []
        self.trade_history = []
        
        # Trading parameters
        self.commission = config.get_float('backtesting', 'commission', 0.001)
        self.slippage = config.get_float('backtesting', 'slippage', 0.0005)
        
        self.running = False
    
    def start_trading(self, symbol: str, timeframe: str = '1h'):
        """
        Start paper trading.
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
        """
        self.logger.info(f"Starting paper trading: {symbol}")
        
        try:
            # Connect to exchange
            if not self.exchange.connect():
                raise Exception("Failed to connect to exchange")
            
            self.running = True
            
            # Main trading loop
            while self.running:
                try:
                    # Get current market data
                    data = self.data_manager.get_ohlcv(symbol, timeframe, limit=100)
                    
                    if data.empty:
                        self.logger.warning("No data available, skipping iteration")
                        time.sleep(60)
                        continue
                    
                    current_price = data['close'].iloc[-1]
                    current_time = datetime.now()
                    
                    # Check risk limits
                    if not self.risk_manager.check_trading_allowed(self.get_portfolio_value()):
                        self.logger.warning("Trading halted due to risk limits")
                        time.sleep(300)  # Wait 5 minutes
                        continue
                    
                    # Generate signals
                    signals = self.strategy.generate_signals(data)
                    
                    # Process signals
                    for signal in signals:
                        if self.strategy.validate_signal(signal):
                            # Check position limits
                            if self.risk_manager.validate_position_size(signal, self.get_portfolio_value()):
                                self._execute_signal(signal, symbol, current_price, current_time)
                    
                    # Check exit conditions for open positions
                    self._check_exit_conditions(symbol, current_price, data.iloc[-1])
                    
                    # Log portfolio status
                    self._log_portfolio_status(symbol, current_price)
                    
                    # Sleep until next iteration
                    sleep_duration = self._get_sleep_duration(timeframe)
                    time.sleep(sleep_duration)
                    
                except KeyboardInterrupt:
                    self.logger.info("Paper trading interrupted by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in trading loop: {str(e)}")
                    time.sleep(60)  # Wait 1 minute before retrying
            
        except Exception as e:
            self.logger.error(f"Paper trading failed: {str(e)}")
        finally:
            self.running = False
            self.logger.info("Paper trading stopped")
    
    def stop_trading(self):
        """Stop paper trading."""
        self.running = False
        self.logger.info("Paper trading stop requested")
    
    def _execute_signal(self, signal, symbol: str, current_price: float, timestamp: datetime):
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal
            symbol: Trading symbol
            current_price: Current market price
            timestamp: Execution timestamp
        """
        try:
            # Calculate position size
            portfolio_value = self.get_portfolio_value()
            position_size = self.strategy.calculate_position_size(signal, portfolio_value, current_price)
            
            # Apply slippage
            if signal.action == 'buy':
                execution_price = current_price * (1 + self.slippage)
            else:
                execution_price = current_price * (1 - self.slippage)
            
            # Calculate costs
            trade_value = position_size * execution_price
            commission_cost = trade_value * self.commission
            total_cost = trade_value + commission_cost
            
            # Check if we have enough cash
            if signal.action == 'buy' and total_cost > self.cash:
                self.logger.warning(f"Insufficient cash for buy order: ${total_cost:.2f} > ${self.cash:.2f}")
                return
            
            # Execute trade
            if signal.action == 'buy':
                self._execute_buy(symbol, position_size, execution_price, commission_cost, timestamp, signal)
            elif signal.action == 'sell':
                self._execute_sell(symbol, position_size, execution_price, commission_cost, timestamp, signal)
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {str(e)}")
    
    def _execute_buy(self, symbol: str, size: float, price: float, commission: float, 
                    timestamp: datetime, signal):
        """Execute buy order."""
        trade_value = size * price
        total_cost = trade_value + commission
        
        # Update cash
        self.cash -= total_cost
        
        # Update position
        if symbol not in self.positions:
            self.positions[symbol] = {
                'size': 0,
                'avg_price': 0,
                'unrealized_pnl': 0,
                'stop_loss': None,
                'take_profit': None
            }
        
        position = self.positions[symbol]
        
        # Calculate new average price
        total_size = position['size'] + size
        if total_size > 0:
            position['avg_price'] = ((position['size'] * position['avg_price']) + (size * price)) / total_size
        
        position['size'] += size
        position['stop_loss'] = signal.stop_loss
        position['take_profit'] = signal.take_profit
        
        # Record trade
        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': 'buy',
            'size': size,
            'price': price,
            'commission': commission,
            'total_cost': total_cost
        }
        
        self.trade_history.append(trade)
        self.logger.info(f"Executed BUY: {size:.6f} {symbol} @ ${price:.2f} (Commission: ${commission:.2f})")
    
    def _execute_sell(self, symbol: str, size: float, price: float, commission: float, 
                     timestamp: datetime, signal):
        """Execute sell order."""
        if symbol not in self.positions or self.positions[symbol]['size'] <= 0:
            self.logger.warning(f"No position to sell for {symbol}")
            return
        
        position = self.positions[symbol]
        sell_size = min(size, position['size'])
        
        trade_value = sell_size * price
        net_proceeds = trade_value - commission
        
        # Calculate realized P&L
        realized_pnl = sell_size * (price - position['avg_price'])
        
        # Update cash
        self.cash += net_proceeds
        
        # Update position
        position['size'] -= sell_size
        
        if position['size'] <= 0:
            # Close position completely
            del self.positions[symbol]
        
        # Record trade
        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': 'sell',
            'size': sell_size,
            'price': price,
            'commission': commission,
            'net_proceeds': net_proceeds,
            'realized_pnl': realized_pnl
        }
        
        self.trade_history.append(trade)
        self.logger.info(f"Executed SELL: {sell_size:.6f} {symbol} @ ${price:.2f} (P&L: ${realized_pnl:.2f})")
    
    def _check_exit_conditions(self, symbol: str, current_price: float, current_data: pd.Series):
        """Check if any positions should be exited."""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Create position dict for strategy
        strategy_position = {
            'side': 'long',
            'size': position['size'],
            'entry_price': position['avg_price'],
            'stop_loss': position['stop_loss'],
            'take_profit': position['take_profit']
        }
        
        # Check strategy exit conditions
        exit_signal = self.strategy.should_exit_position(strategy_position, current_price, current_data)
        
        if exit_signal:
            timestamp = datetime.now()
            commission = position['size'] * current_price * self.commission
            self._execute_sell(symbol, position['size'], current_price, commission, timestamp, exit_signal)
    
    def _log_portfolio_status(self, symbol: str, current_price: float):
        """Log current portfolio status."""
        portfolio_value = self.get_portfolio_value()
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital * 100
        
        position_info = ""
        if symbol in self.positions:
            position = self.positions[symbol]
            unrealized_pnl = position['size'] * (current_price - position['avg_price'])
            position_info = f" | Position: {position['size']:.6f} @ ${position['avg_price']:.2f} (P&L: ${unrealized_pnl:.2f})"
        
        self.logger.info(f"Portfolio: ${portfolio_value:.2f} ({total_return:+.2f}%) | Cash: ${self.cash:.2f}{position_info}")
    
    def _get_sleep_duration(self, timeframe: str) -> int:
        """Get sleep duration based on timeframe."""
        timeframe_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400
        }
        
        return timeframe_map.get(timeframe, 3600)  # Default to 1 hour
    
    def get_portfolio_value(self) -> float:
        """
        Calculate current portfolio value.
        
        Returns:
            Total portfolio value
        """
        total_value = self.cash
        
        # Add position values (would need current prices in real implementation)
        for symbol, position in self.positions.items():
            try:
                ticker = self.exchange.get_ticker(symbol)
                current_price = ticker['last']
                position_value = position['size'] * current_price
                total_value += position_value
            except Exception as e:
                self.logger.warning(f"Could not get current price for {symbol}: {str(e)}")
        
        return total_value
    
    def get_positions(self) -> Dict:
        """Get current positions."""
        return self.positions.copy()
    
    def get_trade_history(self) -> List[Dict]:
        """Get trade history."""
        return self.trade_history.copy()
    
    def get_performance_summary(self) -> Dict:
        """
        Get performance summary.
        
        Returns:
            Performance summary dictionary
        """
        portfolio_value = self.get_portfolio_value()
        total_return = (portfolio_value - self.initial_capital) / self.initial_capital
        
        # Calculate trade statistics
        total_trades = len(self.trade_history)
        profitable_trades = sum(1 for trade in self.trade_history 
                              if trade.get('realized_pnl', 0) > 0)
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': portfolio_value,
            'total_return': total_return,
            'cash': self.cash,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'positions': len(self.positions)
        }
