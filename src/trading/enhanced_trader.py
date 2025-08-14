"""
Enhanced trading implementation with crash protection and advanced risk management.
Integrates the advanced buy/sell logic with peak tracking and dynamic rebuy mechanisms.
"""

import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..strategies.enhanced_bollinger_strategy import EnhancedBollingerBandsStrategy
from ..strategies.bollinger_strategy import BollingerBandsStrategy
from ..data.manager import DataManager
from ..risk.manager import RiskManager
from ..exchanges.base import BaseExchange
from ..config import Config


class EnhancedTrader:
    """Enhanced trader with crash protection and advanced risk management."""
    
    def __init__(self, config: Config, exchange: BaseExchange):
        """Initialize enhanced trader."""
        self.config = config
        self.exchange = exchange
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_manager = DataManager(exchange, cache_enabled=True)
        self.risk_manager = RiskManager(config)
        
        # Select strategy based on configuration
        use_enhanced = config.get_bool('strategy', 'use_enhanced_strategy', True)
        if use_enhanced:
            self.strategy = EnhancedBollingerBandsStrategy(config)
            self.logger.info("Using Enhanced Bollinger Bands Strategy with crash protection")
        else:
            self.strategy = BollingerBandsStrategy(config)
            self.logger.info("Using Standard Bollinger Bands Strategy")
        
        # Trading state
        self.running = False
        self.trade_history = []
        self.equity = config.get_float('backtesting', 'initial_capital', 10000.0)
        
        # Enhanced features
        self.position_state = self.strategy.get_position_state() if hasattr(self.strategy, 'get_position_state') else {
            'position_qty': 0.0,
            'entry_price': 0.0,
            'peak_since_entry': 0.0,
            'rebuy_armed': False,
            'rebuy_price': 0.0,
            'rebuy_ready_at': None
        }
        self.last_update_time = None
        
    def start_trading(self, symbol: str, timeframe: str = '1h'):
        """Start enhanced trading with crash protection."""
        self.logger.info(f"Starting enhanced trading: {symbol} on {timeframe}")
        
        try:
            # Validate connection
            if not self.exchange.connect():
                raise Exception("Failed to connect to exchange")
            
            self.running = True
            
            # Main trading loop with enhanced features
            while self.running:
                try:
                    # Get market data
                    data = self.data_manager.get_ohlcv(symbol, timeframe, limit=100)
                    
                    if data.empty:
                        self.logger.warning("No data available, waiting...")
                        time.sleep(60)
                        continue
                    
                    current_price = data['close'].iloc[-1]
                    current_time = datetime.now()
                    
                    # Update strategy equity if using enhanced strategy
                    if hasattr(self.strategy, 'update_equity'):
                        self.strategy.update_equity(self.equity)
                    
                    # Risk management check
                    if not self.risk_manager.check_trading_allowed(self.equity):
                        self.logger.warning("Trading halted due to risk limits")
                        time.sleep(300)
                        continue
                    
                    # Generate signals using the configured strategy
                    signals = self.strategy.generate_signals(data)
                    
                    # Process signals with enhanced validation
                    for signal in signals:
                        if self._validate_enhanced_signal(signal, symbol, current_price):
                            self._execute_enhanced_signal(signal, symbol, current_price, current_time)
                    
                    # Enhanced position monitoring
                    self._monitor_enhanced_positions(symbol, current_price, data.iloc[-1])
                    
                    # Log enhanced status
                    self._log_enhanced_status(symbol, current_price, current_time)
                    
                    # Update timing
                    self.last_update_time = current_time
                    
                    # Sleep based on timeframe
                    sleep_duration = self._get_sleep_duration(timeframe)
                    time.sleep(sleep_duration)
                    
                except KeyboardInterrupt:
                    self.logger.info("Trading interrupted by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in trading loop: {e}")
                    time.sleep(60)  # Wait before retrying
            
        except Exception as e:
            self.logger.error(f"Enhanced trading failed: {e}")
        finally:
            self.running = False
            self.logger.info("Enhanced trading stopped")
    
    def stop_trading(self):
        """Stop enhanced trading."""
        self.running = False
        self.logger.info("Enhanced trading stop requested")
    
    def _validate_enhanced_signal(self, signal, symbol: str, current_price: float) -> bool:
        """Enhanced signal validation with additional safety checks."""
        # Basic validation
        if not self.strategy.validate_signal(signal):
            return False
        
        # Enhanced confidence threshold for live trading
        min_confidence = 0.65  # Lower than live trading due to enhanced safety features
        if signal.confidence < min_confidence:
            self.logger.debug(f"Signal confidence below threshold: {signal.confidence:.2f}")
            return False
        
        # Position size validation
        max_position_percent = 0.08  # Max 8% of portfolio per trade
        if signal.size > max_position_percent:
            self.logger.warning(f"Position size too large: {signal.size:.2f}")
            return False
        
        # Enhanced strategy specific validations
        if hasattr(self.strategy, 'get_position_state'):
            position_state = self.strategy.get_position_state()
            
            # Check if rebuy mechanism is properly armed for entry signals
            if signal.action == 'buy' and position_state.get('rebuy_armed', False):
                if not self._validate_rebuy_timing(position_state):
                    return False
        
        return True
    
    def _validate_rebuy_timing(self, position_state: Dict) -> bool:
        """Validate rebuy timing for enhanced strategy."""
        if position_state.get('rebuy_ready_at'):
            try:
                ready_time = position_state['rebuy_ready_at']
                if isinstance(ready_time, str):
                    ready_time = datetime.fromisoformat(ready_time.replace('Z', '+00:00'))
                
                if datetime.now() < ready_time:
                    self.logger.debug("Rebuy cooldown period not yet elapsed")
                    return False
            except Exception as e:
                self.logger.warning(f"Error validating rebuy timing: {e}")
                return False
        
        return True
    
    def _execute_enhanced_signal(self, signal, symbol: str, current_price: float, timestamp: datetime):
        """Execute signal with enhanced tracking and logging."""
        try:
            # Calculate position size in currency units
            position_size_dollars = signal.size * self.equity
            position_size_units = position_size_dollars / current_price
            
            # Enhanced logging for different signal types
            event_type = getattr(signal, 'metadata', {}).get('event', 'UNKNOWN')
            
            # Simulate order execution (paper trading)
            if signal.action == 'buy':
                # Update equity and position tracking
                fees = position_size_dollars * 0.001  # 0.1% fee
                total_cost = position_size_dollars + fees
                
                if total_cost <= self.equity:
                    self.equity -= total_cost
                    
                    # Log trade with enhanced details
                    trade_record = {
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'action': signal.action,
                        'size': position_size_units,
                        'price': current_price,
                        'confidence': signal.confidence,
                        'event_type': event_type,
                        'stop_loss': signal.stop_loss,
                        'take_profit': signal.take_profit,
                        'equity_after': self.equity
                    }
                    
                    self.trade_history.append(trade_record)
                    
                    self.logger.info(f"[{event_type}] BUY {position_size_units:.6f} {symbol} @ ${current_price:.2f} "
                                   f"(Confidence: {signal.confidence:.2f}, Equity: ${self.equity:.2f})")
                    
                    # Enhanced metadata logging
                    if hasattr(signal, 'metadata') and signal.metadata:
                        metadata_str = ", ".join([f"{k}={v}" for k, v in signal.metadata.items() if k != 'event'])
                        if metadata_str:
                            self.logger.debug(f"Signal metadata: {metadata_str}")
                
            elif signal.action == 'sell':
                # Calculate PnL if available in metadata
                pnl = getattr(signal, 'metadata', {}).get('pnl', 0)
                sale_proceeds = position_size_units * current_price
                fees = sale_proceeds * 0.001
                net_proceeds = sale_proceeds - fees
                
                self.equity += net_proceeds
                
                trade_record = {
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'action': signal.action,
                    'size': position_size_units,
                    'price': current_price,
                    'confidence': signal.confidence,
                    'event_type': event_type,
                    'pnl': pnl,
                    'equity_after': self.equity
                }
                
                self.trade_history.append(trade_record)
                
                self.logger.info(f"[{event_type}] SELL {position_size_units:.6f} {symbol} @ ${current_price:.2f} "
                               f"(PnL: ${pnl:.2f}, Equity: ${self.equity:.2f})")
        
        except Exception as e:
            self.logger.error(f"Failed to execute enhanced signal: {e}")
    
    def _monitor_enhanced_positions(self, symbol: str, current_price: float, current_data: pd.Series):
        """Enhanced position monitoring with crash detection."""
        if hasattr(self.strategy, 'get_position_state'):
            position_state = self.strategy.get_position_state()
            
            # Log position state changes
            if position_state.get('position_qty', 0) > 0:
                entry_price = position_state.get('entry_price', 0)
                peak_since_entry = position_state.get('peak_since_entry', 0)
                
                if entry_price > 0:
                    unrealized_pnl = (current_price - entry_price) / entry_price * 100
                    peak_drawdown = (peak_since_entry - current_price) / peak_since_entry * 100 if peak_since_entry > 0 else 0
                    
                    self.logger.debug(f"Position monitoring: Price=${current_price:.2f}, "
                                    f"Entry=${entry_price:.2f}, Peak=${peak_since_entry:.2f}, "
                                    f"Unrealized PnL: {unrealized_pnl:.2f}%, "
                                    f"Peak DD: {peak_drawdown:.2f}%")
            
            # Monitor rebuy state
            if position_state.get('rebuy_armed', False):
                rebuy_price = position_state.get('rebuy_price', 0)
                ready_time = position_state.get('rebuy_ready_at')
                
                status = "READY" if ready_time and datetime.now() >= ready_time else "COOLDOWN"
                self.logger.debug(f"Rebuy armed: Price=${rebuy_price:.2f}, Status={status}")
    
    def _log_enhanced_status(self, symbol: str, current_price: float, timestamp: datetime):
        """Enhanced status logging with detailed information."""
        if hasattr(self.strategy, 'get_position_state'):
            position_state = self.strategy.get_position_state()
            position_qty = position_state.get('position_qty', 0)
            
            status_parts = [
                f"Enhanced Trading Status",
                f"Symbol: {symbol}",
                f"Price: ${current_price:.2f}",
                f"Equity: ${self.equity:.2f}",
                f"Position: {position_qty:.6f}" if position_qty > 0 else "Position: FLAT",
                f"Rebuy: {'ARMED' if position_state.get('rebuy_armed', False) else 'DISARMED'}"
            ]
            
            self.logger.info(" | ".join(status_parts))
    
    def _get_sleep_duration(self, timeframe: str) -> int:
        """Get appropriate sleep duration based on timeframe."""
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
    
    def get_trading_statistics(self) -> Dict:
        """Get enhanced trading statistics."""
        if not self.trade_history:
            return {}
        
        trades_df = pd.DataFrame(self.trade_history)
        
        # Basic statistics
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['action'] == 'buy'])
        sell_trades = len(trades_df[trades_df['action'] == 'sell'])
        
        # Enhanced statistics
        crash_exits = len(trades_df[trades_df['event_type'] == 'CRASH_EXIT'])
        rebuy_trades = len(trades_df[trades_df['event_type'].str.contains('REBUY', na=False)])
        normal_exits = len(trades_df[trades_df['event_type'] == 'NORMAL_EXIT'])
        
        # PnL analysis
        total_pnl = trades_df['pnl'].sum() if 'pnl' in trades_df.columns else 0
        
        # Current position state
        position_state = {}
        if hasattr(self.strategy, 'get_position_state'):
            position_state = self.strategy.get_position_state()
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'crash_exits': crash_exits,
            'rebuy_trades': rebuy_trades,
            'normal_exits': normal_exits,
            'total_pnl': total_pnl,
            'current_equity': self.equity,
            'position_state': position_state,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None
        }
    
    def emergency_stop(self):
        """Enhanced emergency stop with position state reset."""
        self.logger.critical("Enhanced emergency stop activated")
        
        # Reset position state if using enhanced strategy
        if hasattr(self.strategy, 'get_position_state'):
            position_state = self.strategy.get_position_state()
            position_state.update({
                'position_qty': 0.0,
                'entry_price': 0.0,
                'peak_since_entry': 0.0,
                'rebuy_armed': False,
                'rebuy_price': 0.0,
                'rebuy_ready_at': None
            })
        
        self.stop_trading()
        self.logger.critical("Enhanced emergency stop completed")