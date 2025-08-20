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
            import os
            
            # Get credentials directly from environment variables
            api_key = os.getenv('OKX_API_KEY', '')
            secret_key = os.getenv('OKX_SECRET_KEY', '')
            passphrase = os.getenv('OKX_PASSPHRASE', '')
            
            if not all([api_key, secret_key, passphrase]):
                raise Exception("Missing OKX API credentials in environment variables")
            
            # Check if demo mode is enabled (default to demo for compatibility)
            demo_mode = os.getenv('OKX_DEMO', '1').strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')
            
            self.exchange = ccxt.okx({
                'apiKey': api_key,
                'secret': secret_key,
                'password': passphrase,
                'sandbox': demo_mode,  # Use demo mode by default for compatibility
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'spot'  # Use spot trading by default
                }
            })
            
            # Add simulated trading header for demo mode
            if demo_mode:
                self.exchange.headers = {**(self.exchange.headers or {}), 'x-simulated-trading': '1'}
                self.logger.info("Using OKX Demo/Sandbox mode")
            
            # Test connection
            self.exchange.load_markets()
            self.logger.info("Successfully connected to OKX")
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
            elif "50103" in error_msg:
                self.logger.error("OKX Error 50103: Invalid signature. Check secret key and passphrase")
            elif "50104" in error_msg:
                self.logger.error("OKX Error 50104: Invalid passphrase")
            elif "50105" in error_msg:
                self.logger.error("OKX Error 50105: Timestamp request expired")
            elif "50111" in error_msg:
                self.logger.error("OKX Error 50111: Invalid IP address (not whitelisted)")
            
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
    
    def get_balance(self) -> Dict:
        """
        Get account balance from OKX.
        
        Returns:
            Account balance data
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            balance = self.exchange.fetch_balance()
            return dict(balance)
            
        except Exception as e:
            self.logger.error(f"Error fetching balance: {str(e)}")
            raise
    
    def get_positions(self) -> List[Dict]:
        """
        Get open positions from OKX.
        In demo mode, returns simulated portfolio positions.
        
        Returns:
            List of position data
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            # Check if we're in demo mode
            demo_mode = os.getenv('OKX_DEMO', '1').strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')
            
            if demo_mode:
                # Return simulated positions for demo mode
                return self._get_demo_positions()
            else:
                # Try to fetch real positions
                positions = self.exchange.fetch_positions()
                return [dict(pos) for pos in positions if pos['contracts'] > 0]
            
        except Exception as e:
            self.logger.error(f"Error fetching positions: {str(e)}")
            # If real API fails, fall back to demo positions in demo mode
            demo_mode = os.getenv('OKX_DEMO', '1').strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')
            if demo_mode:
                self.logger.info("Falling back to demo positions due to API error")
                return self._get_demo_positions()
            raise
    
    def get_trades(self, symbol: Optional[str] = None, since: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """
        Get trade history from OKX.
        
        Args:
            symbol: Optional symbol filter
            since: Optional timestamp filter
            limit: Number of trades to return
            
        Returns:
            List of trade data
        """
        try:
            if not self.is_connected():
                raise Exception("Not connected to exchange")
            
            trades = self.exchange.fetch_my_trades(symbol, since, limit)
            return [dict(trade) for trade in trades]
            
        except Exception as e:
            self.logger.error(f"Error fetching trades: {str(e)}")
            raise
    
    def _get_demo_positions(self) -> List[Dict]:
        """
        Generate simulated positions for demo mode.
        Creates $10 positions for each of the 103 assets.
        
        Returns:
            List of simulated position data
        """
        import random
        from datetime import datetime
        from src.data.portfolio_assets import MASTER_PORTFOLIO_ASSETS
        
        positions = []
        
        for i, symbol in enumerate(MASTER_PORTFOLIO_ASSETS):
            # Simulate realistic crypto prices
            if symbol == "BTC":
                price = 45000 + random.uniform(-2000, 2000)
            elif symbol == "ETH":
                price = 2800 + random.uniform(-200, 200)
            elif symbol == "SOL":
                price = 85 + random.uniform(-10, 10)
            elif symbol in ["XRP", "ADA", "DOGE", "MATIC"]:
                price = random.uniform(0.30, 1.50)
            elif symbol in ["LINK", "UNI", "AVAX", "DOT"]:
                price = random.uniform(8, 25)
            elif symbol in ["SHIB", "PEPE", "FLOKI"]:
                price = random.uniform(0.000001, 0.001)
            else:
                # General altcoin range
                price = random.uniform(0.1, 100)
            
            # Calculate quantity for $10 position
            quantity = 10.0 / price
            
            # Add some realistic P&L variation
            current_price = price * random.uniform(0.95, 1.05)
            unrealized_pnl = (current_price - price) * quantity
            
            position = {
                'symbol': f"{symbol}/USDT",
                'id': f"demo-{i+1}",
                'timestamp': datetime.now().timestamp() * 1000,
                'datetime': datetime.now().isoformat(),
                'contracts': quantity,
                'contractSize': 1,
                'side': 'long',
                'size': quantity,
                'notional': current_price * quantity,
                'percentage': (unrealized_pnl / 10.0) * 100,
                'unrealizedPnl': unrealized_pnl,
                'realizedPnl': 0,
                'collateral': 10.0,
                'markPrice': current_price,
                'entryPrice': price,
                'liquidationPrice': None,
                'hedged': False,
                'maintenanceMargin': 0,
                'maintenanceMarginPercentage': 0,
                'initialMargin': 0,
                'initialMarginPercentage': 0,
                'leverage': 1,
                'info': {
                    'instType': 'SPOT',
                    'instId': f"{symbol}-USDT",
                    'pos': str(quantity),
                    'posCcy': symbol,
                    'posId': f"demo-{i+1}",
                    'avgPx': str(price),
                    'markPx': str(current_price),
                    'upl': str(unrealized_pnl),
                    'uplRatio': str((unrealized_pnl / 10.0)),
                    'cTime': str(int(datetime.now().timestamp() * 1000))
                }
            }
            
            positions.append(position)
        
        return positions
