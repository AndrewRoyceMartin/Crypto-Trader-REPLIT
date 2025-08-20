"""
OKX exchange adapter for live trading.
"""

import ccxt
import pandas as pd
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base import BaseExchange


class OKXAdapter(BaseExchange):
    """OKX exchange adapter for live trading."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OKX adapter with configuration."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.exchange: Optional[ccxt.okx] = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """Connect to OKX exchange."""
        try:
            # Get credentials from environment or config
            api_key = os.getenv("OKX_API_KEY") or self.config.get("apiKey", "")
            secret_key = os.getenv("OKX_SECRET_KEY") or os.getenv("OKX_API_SECRET") or self.config.get("secret", "")
            passphrase = os.getenv("OKX_PASSPHRASE") or os.getenv("OKX_API_PASSPHRASE") or self.config.get("password", "")
            
            # 🌍 Regional endpoint support (2024 OKX update)
            hostname = os.getenv("OKX_HOSTNAME") or os.getenv("OKX_REGION") or "www.okx.com"
            
            if not all([api_key, secret_key, passphrase]):
                raise Exception("Missing OKX API credentials in environment variables")
            
            # Always use live trading mode
            demo_mode = False
            
            self.exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': secret_key,
                'password': passphrase,
                'hostname': hostname,  # Regional endpoint support
                'sandbox': False,  # Always use live trading
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot'  # Use spot trading by default
                }
            })
            
            # Always use live trading mode
            self.logger.info("Using OKX Live Trading mode")
            
            # Test connection
            self.exchange.load_markets()
            self.logger.info("Successfully connected to OKX")
            self._is_connected = True
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to connect to OKX: {error_msg}")
            
            # Provide specific guidance for common errors
            if "50119" in error_msg:
                self.logger.error("OKX Error 50119: API key doesn't exist. This usually means:")
                self.logger.error("1. API key was created for demo/testnet but connecting to live trading")
                self.logger.error("2. API key lacks required permissions (need Read + Trade)")
                self.logger.error("3. IP address not whitelisted")
                self.logger.error("4. API key was disabled or incorrectly copied")
                self.logger.error("5. FOR AUSTRALIA: ASIC-compliant verification not completed")
                self.logger.error("See OKX_API_SETUP_GUIDE.md for detailed fix instructions")
            
            self._is_connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to exchange."""
        return self._is_connected and self.exchange is not None
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"Error fetching balance: {str(e)}")
            raise
    
    def get_positions(self) -> List[Dict]:
        """
        Get open positions from OKX.
        Returns live portfolio positions from OKX account.
        
        Returns:
            List of position data
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            # Fetch real positions from OKX account
            positions = self.exchange.fetch_positions()
            return [dict(pos) for pos in positions if pos['contracts'] > 0]
            
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            raise
    
    def place_order(self, symbol: str, side: str, amount: float, order_type: str = "market", price: Optional[float] = None) -> Dict[str, Any]:
        """Place an order on the exchange."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            if order_type == "market":
                order = self.exchange.create_market_order(symbol, side, amount)
            elif order_type == "limit" and price is not None:
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                raise ValueError("Invalid order type or missing price for limit order")
            
            return order
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            raise
    
    def get_trades(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            # OKX has strict limits - try smaller limit and specific symbol first
            if symbol:
                trades = self.exchange.fetch_my_trades(symbol, limit=min(limit, 50))
            else:
                # For OKX, don't fetch all symbols at once, use smaller limit
                trades = self.exchange.fetch_my_trades(limit=min(limit, 20))
            
            return [dict(trade) for trade in trades]
        except Exception as e:
            self.logger.error(f"Error fetching trades: {str(e)}")
            # Try even smaller limit if first attempt fails
            try:
                if symbol:
                    trades = self.exchange.fetch_my_trades(symbol, limit=10)
                else:
                    trades = self.exchange.fetch_my_trades(limit=10)
                return [dict(trade) for trade in trades]
            except Exception as e2:
                self.logger.error(f"Error with smaller limit: {str(e2)}")
                raise e
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return dict(ticker)
        except Exception as e:
            self.logger.error(f"Error fetching ticker: {str(e)}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return [dict(order) for order in orders]
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {str(e)}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order."""
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            return dict(result)
        except Exception as e:
            self.logger.error(f"Error canceling order: {str(e)}")
            raise


def make_okx_spot() -> ccxt.okx:
    """
    Return a ccxt OKX client configured for SPOT trading in production mode.
    """
    api_key = os.getenv("OKX_API_KEY", "")
    api_secret = os.getenv("OKX_API_SECRET") or os.getenv("OKX_SECRET_KEY", "")
    passphrase = os.getenv("OKX_API_PASSPHRASE") or os.getenv("OKX_PASSPHRASE", "")
    
    if not all([api_key, api_secret, passphrase]):
        raise RuntimeError("OKX API credentials required. Check OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE")
    
    # Always use production mode
    use_demo = False
    
    ex = ccxt.okx({
        "enableRateLimit": True,
        "apiKey": api_key,
        "secret": api_secret,
        "password": passphrase,
        "sandbox": use_demo,  # Always False for production
    })
    
    # Force SPOT trading
    ex.options = {**getattr(ex, "options", {}), "defaultType": "spot"}
    
    # Load markets
    ex.load_markets()
    return ex
