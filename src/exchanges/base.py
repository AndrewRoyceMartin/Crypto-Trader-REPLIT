"""
Base exchange adapter class.
Defines the interface for exchange adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import pandas as pd


class BaseExchange(ABC):
    """Base class for exchange adapters."""
    
    def __init__(self, config: Dict):
        """
        Initialize exchange adapter.
        
        Args:
            config: Exchange configuration
        """
        self.config = config
        self.exchange = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to exchange.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            limit: Number of candles to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict:
        """
        Get account balance.
        
        Returns:
            Balance dictionary
        """
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, amount: float, 
                   order_type: str = 'market', price: Optional[float] = None) -> Dict:
        """
        Place an order.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            amount: Order amount
            order_type: Order type ('market', 'limit')
            price: Order price (for limit orders)
            
        Returns:
            Order result dictionary
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            Cancellation result
        """
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data
        """
        pass
    
    def format_symbol(self, symbol: str) -> str:
        """
        Format symbol for exchange.
        
        Args:
            symbol: Symbol in standard format (BTC/USDT)
            
        Returns:
            Exchange-specific symbol format
        """
        return symbol
    
    def is_connected(self) -> bool:
        """Check if exchange is connected."""
        return self.exchange is not None
