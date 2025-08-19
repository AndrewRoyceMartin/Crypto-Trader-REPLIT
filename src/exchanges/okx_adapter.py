"""
OKX exchange adapter for demo trading.
"""

import ccxt
import pandas as pd
import logging
from typing import Dict, List, Optional
from .base import BaseExchange


class OKXAdapter(BaseExchange):
    """OKX exchange adapter."""
    
    def __init__(self, config: Dict):
        """
        Initialize OKX adapter.
        
        Args:
            config: Exchange configuration
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """
        Connect to OKX exchange.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.exchange = ccxt.okx({
                'apiKey': self.config.get('apiKey', ''),
                'secret': self.config.get('secret', ''),
                'password': self.config.get('password', ''),
                'sandbox': self.config.get('sandbox', True),
                'enableRateLimit': True,
            })
            
            # Test connection
            self.exchange.load_markets()
            self.logger.info("Successfully connected to OKX")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to OKX: {str(e)}")
            return False
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data from OKX.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Number of candles
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            import pandas as pd
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  # type: ignore[call-arg]
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data: {str(e)}")
            raise
    
    def get_balance(self) -> Dict:
        """
        Get account balance.
        
        Returns:
            Balance dictionary
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            balance = self.exchange.fetch_balance()
            return balance
            
        except Exception as e:
            self.logger.error(f"Error fetching balance: {str(e)}")
            raise
    
    def place_order(self, symbol: str, side: str, amount: float, 
                   order_type: str = 'market', price: Optional[float] = None) -> Dict:
        """
        Place an order on OKX.
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            amount: Order amount
            order_type: Order type
            price: Order price
            
        Returns:
            Order result
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price
            )
            
            self.logger.info(f"Order placed: {order['id']} - {side} {amount} {symbol}")
            return dict(order)
            
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            orders = self.exchange.fetch_open_orders(symbol)
            return [dict(order) for order in orders]
            
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {str(e)}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
            symbol: Trading symbol
            
        Returns:
            Cancellation result
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            result = self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order cancelled: {order_id}")
            return dict(result) if hasattr(result, '__dict__') or hasattr(result, 'keys') else {"status": "cancelled", "id": order_id}
            
        except Exception as e:
            self.logger.error(f"Error cancelling order: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get ticker data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Ticker data
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            ticker = self.exchange.fetch_ticker(symbol)
            return dict(ticker)
            
        except Exception as e:
            self.logger.error(f"Error fetching ticker: {str(e)}")
            raise
