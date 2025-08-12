"""
Live trading implementation with real money.
"""

import pandas as pd
import logging
import time
from datetime import datetime
from typing import Dict, List
from ..data.manager import DataManager
from ..strategies.base import BaseStrategy
from ..risk.manager import RiskManager
from ..exchanges.kraken_adapter import KrakenAdapter


class LiveTrader:
    """Live trading with real money."""
    
    def __init__(self, config, strategy: BaseStrategy):
        """
        Initialize live trader.
        
        Args:
            config: Configuration object
            strategy: Trading strategy
        """
        self.config = config
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
        # Initialize exchange and data manager
        exchange_config = config.get_exchange_config('kraken')
        self.exchange = KrakenAdapter(exchange_config)
        self.data_manager = DataManager(self.exchange, cache_enabled=True)
        
        # Initialize risk manager
        self.risk_manager = RiskManager(config)
        
        # Trading state
        self.orders = []
        self.trade_history = []
        self.running = False
        
        # Safety checks
        self.max_daily_trades = 50
        self.daily_trade_count = 0
        self.last_trade_date = None
    
    def start_trading(self, symbol: str, timeframe: str = '1h'):
        """
        Start live trading.
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
        """
        self.logger.critical(f"STARTING LIVE TRADING WITH REAL MONEY: {symbol}")
        
        # Additional safety confirmation
        self.logger.warning("This will execute real trades with real money!")
        time.sleep(5)  # Give user time to cancel
        
        try:
            # Connect to exchange
            if not self.exchange.connect():
                raise Exception("Failed to connect to exchange")
            
            # Validate account and check balance
            balance = self.exchange.get_balance()
            self.logger.info(f"Account balance: {balance}")
            
            # Check if we have sufficient funds
            usd_balance = balance.get('free', {}).get('USD', 0)
            if usd_balance < 100:  # Minimum $100
                raise Exception(f"Insufficient funds: ${usd_balance}")
            
            self.running = True
            
            # Main trading loop
            while self.running:
                try:
                    # Reset daily trade count if new day
                    current_date = datetime.now().date()
                    if self.last_trade_date != current_date:
                        self.daily_trade_count = 0
                        self.last_trade_date = current_date
                    
                    # Check daily trade limit
                    if self.daily_trade_count >= self.max_daily_trades:
                        self.logger.warning("Daily trade limit reached, waiting until tomorrow")
                        time.sleep(3600)  # Wait 1 hour
                        continue
                    
                    # Get current market data
                    data = self.data_manager.get_ohlcv(symbol, timeframe, limit=100)
                    
                    if data.empty:
                        self.logger.warning("No data available, skipping iteration")
                        time.sleep(60)
                        continue
                    
                    current_price = data['close'].iloc[-1]
                    
                    # Check risk limits
                    portfolio_value = self._get_portfolio_value()
                    if not self.risk_manager.check_trading_allowed(portfolio_value):
                        self.logger.warning("Trading halted due to risk limits")
                        time.sleep(300)  # Wait 5 minutes
                        continue
                    
                    # Generate signals
                    signals = self.strategy.generate_signals(data)
                    
                    # Process signals with extra caution
                    for signal in signals:
                        if self._validate_live_signal(signal, symbol, portfolio_value):
                            self._execute_live_signal(signal, symbol, current_price)
                    
                    # Check and manage open positions
                    self._manage_open_positions(symbol, current_price, data.iloc[-1])
                    
                    # Log status
                    self._log_trading_status(symbol, current_price)
                    
                    # Sleep until next iteration
                    sleep_duration = self._get_sleep_duration(timeframe)
                    time.sleep(sleep_duration)
                    
                except KeyboardInterrupt:
                    self.logger.critical("Live trading interrupted by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in live trading loop: {str(e)}")
                    time.sleep(300)  # Wait 5 minutes before retrying
            
        except Exception as e:
            self.logger.critical(f"Live trading failed: {str(e)}")
        finally:
            self.running = False
            self.logger.critical("Live trading stopped")
    
    def stop_trading(self):
        """Stop live trading."""
        self.running = False
        self.logger.critical("Live trading stop requested")
    
    def _validate_live_signal(self, signal, symbol: str, portfolio_value: float) -> bool:
        """
        Validate signal for live trading with extra safety checks.
        
        Args:
            signal: Trading signal
            symbol: Trading symbol
            portfolio_value: Current portfolio value
            
        Returns:
            True if signal is safe to execute
        """
        # Basic signal validation
        if not self.strategy.validate_signal(signal):
            return False
        
        # Risk manager validation
        if not self.risk_manager.validate_position_size(signal, portfolio_value):
            self.logger.warning("Signal rejected by risk manager")
            return False
        
        # Additional live trading safety checks
        
        # Check if signal confidence is high enough
        min_confidence = 0.7  # Require high confidence for live trading
        if signal.confidence < min_confidence:
            self.logger.warning(f"Signal confidence too low: {signal.confidence} < {min_confidence}")
            return False
        
        # Check position size is reasonable
        max_position_percent = 0.1  # Max 10% of portfolio per trade
        if signal.size > max_position_percent:
            self.logger.warning(f"Position size too large: {signal.size} > {max_position_percent}")
            return False
        
        # Check we haven't traded this symbol recently
        recent_trades = [t for t in self.trade_history 
                        if t['symbol'] == symbol and 
                        (datetime.now() - t['timestamp']).seconds < 3600]  # 1 hour
        
        if len(recent_trades) >= 3:
            self.logger.warning(f"Too many recent trades for {symbol}")
            return False
        
        return True
    
    def _execute_live_signal(self, signal, symbol: str, current_price: float):
        """
        Execute signal in live trading.
        
        Args:
            signal: Trading signal
            symbol: Trading symbol
            current_price: Current market price
        """
        try:
            portfolio_value = self._get_portfolio_value()
            position_size = self.strategy.calculate_position_size(signal, portfolio_value, current_price)
            
            # Additional safety: limit position size
            max_size_usd = portfolio_value * 0.05  # Max 5% of portfolio
            max_size_units = max_size_usd / current_price
            position_size = min(position_size, max_size_units)
            
            # Place order on exchange
            order_type = 'market'  # Use market orders for immediate execution
            
            self.logger.critical(f"PLACING LIVE ORDER: {signal.action} {position_size:.6f} {symbol} @ market price")
            
            order = self.exchange.place_order(
                symbol=symbol,
                side=signal.action,
                amount=position_size,
                order_type=order_type
            )
            
            # Record order
            trade_record = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': signal.action,
                'size': position_size,
                'order_id': order['id'],
                'status': 'placed',
                'signal_confidence': signal.confidence
            }
            
            self.orders.append(order)
            self.trade_history.append(trade_record)
            self.daily_trade_count += 1
            
            self.logger.critical(f"LIVE ORDER PLACED: {order['id']} - {signal.action} {position_size:.6f} {symbol}")
            
            # Set stop loss and take profit if specified
            if signal.stop_loss or signal.take_profit:
                self._set_stop_orders(symbol, position_size, signal)
            
        except Exception as e:
            self.logger.error(f"Failed to execute live signal: {str(e)}")
    
    def _set_stop_orders(self, symbol: str, position_size: float, signal):
        """Set stop loss and take profit orders."""
        try:
            if signal.stop_loss:
                stop_order = self.exchange.place_order(
                    symbol=symbol,
                    side='sell' if signal.action == 'buy' else 'buy',
                    amount=position_size,
                    order_type='stop_loss',
                    price=signal.stop_loss
                )
                self.logger.info(f"Stop loss set: {stop_order['id']} @ {signal.stop_loss}")
            
            if signal.take_profit:
                tp_order = self.exchange.place_order(
                    symbol=symbol,
                    side='sell' if signal.action == 'buy' else 'buy',
                    amount=position_size,
                    order_type='take_profit',
                    price=signal.take_profit
                )
                self.logger.info(f"Take profit set: {tp_order['id']} @ {signal.take_profit}")
                
        except Exception as e:
            self.logger.warning(f"Failed to set stop orders: {str(e)}")
    
    def _manage_open_positions(self, symbol: str, current_price: float, current_data: pd.Series):
        """Manage open positions and orders."""
        try:
            # Check open orders
            open_orders = self.exchange.get_open_orders(symbol)
            
            # Check if any orders need to be cancelled or modified
            for order in open_orders:
                # Add position management logic here
                pass
            
        except Exception as e:
            self.logger.error(f"Error managing positions: {str(e)}")
    
    def _get_portfolio_value(self) -> float:
        """Get current portfolio value."""
        try:
            balance = self.exchange.get_balance()
            
            # Calculate total value in USD
            total_value = 0
            
            for currency, amounts in balance['free'].items():
                if currency == 'USD':
                    total_value += amounts
                else:
                    # Convert to USD (simplified - would need proper conversion rates)
                    try:
                        ticker = self.exchange.get_ticker(f"{currency}/USD")
                        total_value += amounts * ticker['last']
                    except:
                        pass  # Skip if can't convert
            
            return total_value
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio value: {str(e)}")
            return 0.0
    
    def _log_trading_status(self, symbol: str, current_price: float):
        """Log current trading status."""
        portfolio_value = self._get_portfolio_value()
        
        self.logger.info(f"LIVE TRADING STATUS - Portfolio: ${portfolio_value:.2f} | "
                        f"{symbol}: ${current_price:.2f} | Daily trades: {self.daily_trade_count}")
    
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
    
    def get_open_orders(self) -> List[Dict]:
        """Get open orders."""
        try:
            return self.exchange.get_open_orders()
        except Exception as e:
            self.logger.error(f"Error getting open orders: {str(e)}")
            return []
    
    def cancel_all_orders(self, symbol: str = None):
        """Cancel all open orders."""
        try:
            open_orders = self.exchange.get_open_orders(symbol)
            
            for order in open_orders:
                result = self.exchange.cancel_order(order['id'], order['symbol'])
                self.logger.info(f"Cancelled order: {order['id']}")
                
        except Exception as e:
            self.logger.error(f"Error cancelling orders: {str(e)}")
    
    def emergency_stop(self):
        """Emergency stop - cancel all orders and close positions."""
        self.logger.critical("EMERGENCY STOP ACTIVATED")
        
        try:
            # Cancel all open orders
            self.cancel_all_orders()
            
            # Close all positions (simplified - would need proper position tracking)
            balance = self.exchange.get_balance()
            
            for currency, amounts in balance['free'].items():
                if currency != 'USD' and amounts > 0:
                    try:
                        symbol = f"{currency}/USD"
                        self.exchange.place_order(
                            symbol=symbol,
                            side='sell',
                            amount=amounts,
                            order_type='market'
                        )
                        self.logger.critical(f"Emergency sell: {amounts} {currency}")
                    except Exception as e:
                        self.logger.error(f"Failed to emergency sell {currency}: {str(e)}")
            
        except Exception as e:
            self.logger.critical(f"Emergency stop failed: {str(e)}")
        finally:
            self.stop_trading()
