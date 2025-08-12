"""
Base strategy class.
Defines the interface for trading strategies.
"""

from abc import ABC, abstractmethod
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple


class Signal:
    """Trading signal class."""
    
    def __init__(self, action: str, price: float, size: float, confidence: float = 1.0, 
                 stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        """
        Initialize trading signal.
        
        Args:
            action: 'buy', 'sell', or 'hold'
            price: Signal price
            size: Position size (percentage of portfolio)
            confidence: Signal confidence (0.0 to 1.0)
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        self.action = action
        self.price = price
        self.size = size
        self.confidence = confidence
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.timestamp = pd.Timestamp.now()


class BaseStrategy(ABC):
    """Base class for trading strategies."""
    
    def __init__(self, config):
        """
        Initialize strategy.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.positions = {}  # Track open positions
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals based on market data.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            List of trading signals
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Signal, portfolio_value: float, 
                              current_price: float) -> float:
        """
        Calculate position size for a signal.
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            current_price: Current market price
            
        Returns:
            Position size in base currency units
        """
        pass
    
    def should_exit_position(self, position: Dict, current_price: float, 
                           current_data: pd.Series) -> Optional[Signal]:
        """
        Check if position should be exited.
        
        Args:
            position: Position dictionary
            current_price: Current market price
            current_data: Current market data
            
        Returns:
            Exit signal if position should be closed, None otherwise
        """
        # Check stop loss
        if position['side'] == 'long' and position.get('stop_loss'):
            if current_price <= position['stop_loss']:
                return Signal('sell', current_price, position['size'], 1.0)
        
        if position['side'] == 'short' and position.get('stop_loss'):
            if current_price >= position['stop_loss']:
                return Signal('buy', current_price, position['size'], 1.0)
        
        # Check take profit
        if position['side'] == 'long' and position.get('take_profit'):
            if current_price >= position['take_profit']:
                return Signal('sell', current_price, position['size'], 1.0)
        
        if position['side'] == 'short' and position.get('take_profit'):
            if current_price <= position['take_profit']:
                return Signal('buy', current_price, position['size'], 1.0)
        
        return None
    
    def update_position(self, symbol: str, signal: Signal, execution_price: float):
        """
        Update position tracking.
        
        Args:
            symbol: Trading symbol
            signal: Executed signal
            execution_price: Actual execution price
        """
        if symbol not in self.positions:
            self.positions[symbol] = []
        
        if signal.action in ['buy', 'sell']:
            position = {
                'side': 'long' if signal.action == 'buy' else 'short',
                'size': signal.size,
                'entry_price': execution_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'timestamp': signal.timestamp
            }
            self.positions[symbol].append(position)
            
            self.logger.info(f"Position opened: {symbol} {signal.action} {signal.size} @ {execution_price}")
    
    def close_position(self, symbol: str, position_idx: int, exit_price: float):
        """
        Close a position.
        
        Args:
            symbol: Trading symbol
            position_idx: Position index
            exit_price: Exit price
        """
        if symbol in self.positions and position_idx < len(self.positions[symbol]):
            position = self.positions[symbol].pop(position_idx)
            
            # Calculate P&L
            if position['side'] == 'long':
                pnl = (exit_price - position['entry_price']) * position['size']
            else:
                pnl = (position['entry_price'] - exit_price) * position['size']
            
            self.logger.info(f"Position closed: {symbol} P&L: {pnl:.2f}")
            return pnl
        
        return 0.0
    
    def get_open_positions(self, symbol: Optional[str] = None) -> Dict:
        """
        Get open positions.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            Dictionary of open positions
        """
        if symbol:
            return {symbol: self.positions.get(symbol, [])}
        return self.positions.copy()
    
    def validate_signal(self, signal: Signal) -> bool:
        """
        Validate a trading signal.
        
        Args:
            signal: Signal to validate
            
        Returns:
            True if signal is valid, False otherwise
        """
        # Basic validation
        if signal.action not in ['buy', 'sell', 'hold']:
            return False
        
        if signal.price <= 0:
            return False
        
        if signal.size <= 0:
            return False
        
        if not (0.0 <= signal.confidence <= 1.0):
            return False
        
        return True
    
    def get_strategy_parameters(self) -> Dict:
        """
        Get strategy parameters.
        
        Returns:
            Dictionary of strategy parameters
        """
        return {
            'name': self.__class__.__name__,
            'config': self.config.__dict__ if hasattr(self.config, '__dict__') else str(self.config)
        }
