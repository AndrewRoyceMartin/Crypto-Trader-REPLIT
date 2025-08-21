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
        """Get trade history using comprehensive OKX-compatible methods."""
        if not self.is_connected():
            self.logger.warning("Not connected to OKX exchange")
            return []
        
        try:
            # Import and use the enhanced OKX trade retrieval
            from .okx_trade_methods import OKXTradeRetrieval
            trade_retriever = OKXTradeRetrieval(self.exchange, self.logger)
            
            # Get trades using comprehensive method
            trades = trade_retriever.get_trades_comprehensive(symbol, limit)
            
            if not trades:
                self.logger.warning("No trades found via comprehensive OKX API methods")
                return []
            
            # Format trades for consistency with existing code
            formatted_trades = []
            for trade in trades:
                formatted_trade = {
                    'id': trade.get('id', ''),
                    'symbol': trade.get('symbol', ''),
                    'side': trade.get('side', ''),
                    'quantity': trade.get('quantity', 0),
                    'price': trade.get('price', 0),
                    'timestamp': trade.get('timestamp', 0),
                    'datetime': trade.get('datetime', ''),
                    'total_value': trade.get('total_value', 0),
                    'pnl': 0,  # Calculate P&L separately if needed
                    'source': trade.get('source', 'okx')
                }
                formatted_trades.append(formatted_trade)
            
            self.logger.info(f"Successfully retrieved {len(formatted_trades)} formatted trades")
            return formatted_trades
            
        except ImportError as e:
            self.logger.error(f"Could not import OKX trade methods: {e}")
            # Fallback to original method
            return self._get_trades_fallback(symbol, limit)
        except Exception as e:
            self.logger.error(f"Error in comprehensive trade retrieval: {e}")
            # Fallback to original method
            return self._get_trades_fallback(symbol, limit)
    
    def _get_trades_fallback(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fallback trade retrieval method using basic OKX API calls."""
        all_trades = []
        
        # Method 1: Try fetch_my_trades (standard method)
        try:
            self.logger.info(f"Attempting fetch_my_trades with limit={limit}")
            if symbol:
                trades = self.exchange.fetch_my_trades(symbol, limit=min(limit, 50))
            else:
                trades = self.exchange.fetch_my_trades(limit=min(limit, 100))
            
            self.logger.info(f"fetch_my_trades returned {len(trades)} trades")
            all_trades.extend([dict(trade) for trade in trades])
            
        except Exception as e:
            self.logger.warning(f"fetch_my_trades failed: {str(e)}")
        
        # Method 2: Try fetch_closed_orders (OKX specific method)
        try:
            self.logger.info(f"Attempting fetch_closed_orders (OKX-specific method)")
            closed_orders = self.exchange.fetch_closed_orders(limit=min(limit, 100))
            self.logger.info(f"fetch_closed_orders returned {len(closed_orders)} orders")
            
            # Convert filled orders to trade format
            for order in closed_orders:
                if order.get('status') == 'closed' and order.get('filled', 0) > 0:
                    trade = {
                        'id': order.get('id'),
                        'symbol': order.get('symbol'),
                        'side': order.get('side'),
                        'amount': order.get('filled', order.get('amount', 0)),
                        'price': order.get('average', order.get('price', 0)),
                        'cost': order.get('cost', 0),
                        'datetime': order.get('datetime'),
                        'timestamp': order.get('timestamp'),
                        'fee': order.get('fee'),
                        'type': order.get('type', 'market'),
                        'status': 'closed'
                    }
                    all_trades.append(trade)
                    
            self.logger.info(f"Converted {len(closed_orders)} closed orders to trades")
            
        except Exception as e:
            self.logger.warning(f"fetch_closed_orders fallback failed: {str(e)}")
        
        # Method 3: Try fetch_closed_orders with specific symbols that we know exist in portfolio
        for symbol_check in ['PEPE/USDT', 'BTC/USDT']:
            try:
                self.logger.info(f"Attempting fetch_closed_orders for {symbol_check}")
                symbol_orders = self.exchange.fetch_closed_orders(symbol_check, limit=20)
                self.logger.info(f"fetch_closed_orders for {symbol_check} returned {len(symbol_orders)} orders")
                
                for order in symbol_orders:
                    if order.get('status') == 'closed' and order.get('filled', 0) > 0:
                        # Only add if not already in all_trades
                        order_id = order.get('id')
                        if not any(t.get('id') == order_id for t in all_trades):
                            trade = {
                                'id': order_id,
                                'symbol': order.get('symbol'),
                                'side': order.get('side'),
                                'amount': order.get('filled', order.get('amount', 0)),
                                'price': order.get('average', order.get('price', 0)),
                                'cost': order.get('cost', 0),
                                'datetime': order.get('datetime'),
                                'timestamp': order.get('timestamp'),
                                'fee': order.get('fee'),
                                'type': order.get('type', 'market'),
                                'status': 'closed'
                            }
                            all_trades.append(trade)
                            
            except Exception as e:
                self.logger.warning(f"fetch_closed_orders for {symbol_check} failed: {str(e)}")
                
        # Method 4: Try with time range for last 7 days (more focused)
        try:
            from datetime import datetime, timedelta
            since = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            self.logger.info(f"Attempting fetch_closed_orders with time range (last 7 days)")
            
            recent_orders = self.exchange.fetch_closed_orders(since=since, limit=min(limit, 200))
            self.logger.info(f"Time-range fetch_closed_orders returned {len(recent_orders)} orders")
            
            for order in recent_orders:
                if order.get('status') == 'closed' and order.get('filled', 0) > 0:
                    # Only add if not already in all_trades
                    order_id = order.get('id')
                    if not any(t.get('id') == order_id for t in all_trades):
                        trade = {
                            'id': order_id,
                            'symbol': order.get('symbol'),
                            'side': order.get('side'),
                            'amount': order.get('filled', order.get('amount', 0)),
                            'price': order.get('average', order.get('price', 0)),
                            'cost': order.get('cost', 0),
                            'datetime': order.get('datetime'),
                            'timestamp': order.get('timestamp'),
                            'fee': order.get('fee'),
                            'type': order.get('type', 'market'),
                            'status': 'closed'
                        }
                        all_trades.append(trade)
                        
        except Exception as e:
            self.logger.warning(f"Time-range fetch_closed_orders failed: {str(e)}")
        
        # Sort by timestamp (most recent first)
        all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Remove duplicates based on ID
        seen_ids = set()
        unique_trades = []
        for trade in all_trades:
            trade_id = trade.get('id')
            if trade_id and trade_id not in seen_ids:
                seen_ids.add(trade_id)
                unique_trades.append(trade)
        
        self.logger.info(f"Final result: {len(unique_trades)} unique trades after deduplication")
        
        # If we still have no trades, log a helpful message
        if len(unique_trades) == 0:
            self.logger.warning("No trades found via any OKX API method. This could indicate:")
            self.logger.warning("  1. No recent trading activity")
            self.logger.warning("  2. API permissions don't include trade history")
            self.logger.warning("  3. Trades made on different account/subaccount")
            self.logger.warning("  4. Recent trades not yet reflected in API")
        
        return unique_trades[:limit]  # Return only up to the requested limit
    
    def get_trades_by_timeframe(self, timeframe: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trades filtered by timeframe."""
        from datetime import datetime, timedelta
        
        # Calculate since timestamp based on timeframe
        now = datetime.now()
        if timeframe == '24h':
            since = int((now - timedelta(hours=24)).timestamp() * 1000)
        elif timeframe == '3d':
            since = int((now - timedelta(days=3)).timestamp() * 1000)
        elif timeframe == '7d':
            since = int((now - timedelta(days=7)).timestamp() * 1000)
        elif timeframe == '30d':
            since = int((now - timedelta(days=30)).timestamp() * 1000)
        elif timeframe == '90d':
            since = int((now - timedelta(days=90)).timestamp() * 1000)
        elif timeframe == '1y':
            since = int((now - timedelta(days=365)).timestamp() * 1000)
        else:
            # For 'all' or unknown timeframes, use regular get_trades
            return self.get_trades(limit=limit)
        
        if not self.is_connected():
            raise Exception("Not connected to exchange")
        
        all_trades = []
        
        # Method 1: Try fetch_my_trades with since parameter
        try:
            self.logger.info(f"Attempting fetch_my_trades with timeframe={timeframe}, since={since}")
            trades = self.exchange.fetch_my_trades(since=since, limit=min(limit, 100))
            self.logger.info(f"fetch_my_trades returned {len(trades)} trades for timeframe {timeframe}")
            all_trades.extend([dict(trade) for trade in trades])
        except Exception as e:
            self.logger.warning(f"fetch_my_trades with timeframe failed: {str(e)}")
        
        # Method 2: Try fetch_closed_orders with since parameter
        try:
            self.logger.info(f"Attempting fetch_closed_orders with timeframe={timeframe}")
            closed_orders = self.exchange.fetch_closed_orders(since=since, limit=min(limit, 100))
            self.logger.info(f"fetch_closed_orders returned {len(closed_orders)} orders for timeframe {timeframe}")
            
            for order in closed_orders:
                if order.get('status') == 'closed' and order.get('filled', 0) > 0:
                    trade = {
                        'id': order.get('id'),
                        'symbol': order.get('symbol'),
                        'side': order.get('side'),
                        'amount': order.get('filled', order.get('amount', 0)),
                        'price': order.get('average', order.get('price', 0)),
                        'cost': order.get('cost', 0),
                        'datetime': order.get('datetime'),
                        'timestamp': order.get('timestamp'),
                        'fee': order.get('fee'),
                        'type': order.get('type', 'market'),
                        'status': 'closed'
                    }
                    all_trades.append(trade)
        except Exception as e:
            self.logger.warning(f"fetch_closed_orders with timeframe failed: {str(e)}")
        
        # Sort by timestamp (most recent first)
        all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Remove duplicates
        seen_ids = set()
        unique_trades = []
        for trade in all_trades:
            trade_id = trade.get('id')
            if trade_id and trade_id not in seen_ids:
                seen_ids.add(trade_id)
                unique_trades.append(trade)
        
        self.logger.info(f"Timeframe {timeframe} result: {len(unique_trades)} unique trades")
        return unique_trades[:limit]
    
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
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get order history (alias for get_trades)."""
        return self.get_trades(symbol, limit)

    def get_currency_conversion_rates(self) -> dict:
        """Get currency conversion rates from OKX using fiat trading pairs."""
        try:
            if not self.is_connected():
                self.logger.warning("Exchange not connected, cannot get currency rates")
                return {"USD": 1.0}
            
            # Get USDT prices against major fiat currencies from OKX
            rates = {"USD": 1.0}  # Base currency
            
            # OKX fiat pairs - getting fiat price in USDT
            currency_pairs = {
                "EUR": "EUR/USDT",
                "GBP": "GBP/USDT", 
                "AUD": "AUD/USDT"
            }
            
            for currency, pair in currency_pairs.items():
                try:
                    ticker = self.exchange.fetch_ticker(pair)
                    if ticker and ticker.get('last'):
                        # FIAT/USDT price tells us how many USDT one unit of fiat is worth
                        fiat_usdt_price = float(ticker['last'])
                        if fiat_usdt_price > 0:
                            # USD to FIAT rate = FIAT per USD (since USDT ≈ USD)
                            rates[currency] = fiat_usdt_price
                            self.logger.debug(f"OKX rate USD to {currency}: {fiat_usdt_price}")
                except Exception as e:
                    self.logger.warning(f"Could not get OKX rate for {currency}: {e}")
                    # Fallback rates if OKX doesn't have the pair
                    fallback_rates = {"EUR": 0.92, "GBP": 0.79, "AUD": 1.52}
                    rates[currency] = fallback_rates.get(currency, 1.0)
            
            self.logger.info(f"OKX currency conversion rates: {rates}")
            return rates
            
        except Exception as e:
            self.logger.error(f"Error getting OKX currency rates: {e}")
            # Return fallback rates
            return {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "AUD": 1.52}


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
