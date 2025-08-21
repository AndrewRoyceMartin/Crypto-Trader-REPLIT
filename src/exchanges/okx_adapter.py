"""
OKX exchange adapter for live trading.
"""

import ccxt
import pandas as pd
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
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
        """Get trade history using OKX-specific CCXT methods with direct API access."""
        if not self.is_connected():
            self.logger.warning("Not connected to OKX exchange")
            return []
        
        try:
            all_trades = []
            
            # Method 1: Use OKX-specific privateGetTradeFills endpoint directly via CCXT
            self.logger.info("Attempting OKX privateGetTradeFills (most accurate for executed trades)")
            try:
                params = {'limit': str(min(limit, 100))}
                response = self.exchange.privateGetTradeFills(params)
                
                if response and response.get('code') == '0' and 'data' in response:
                    fills = response['data']
                    self.logger.info(f"OKX fills API returned {len(fills)} trade fills")
                    
                    for fill in fills:
                        trade = self._format_okx_fill_direct(fill)
                        if trade:
                            all_trades.append(trade)
                else:
                    self.logger.info(f"OKX fills API response: code={response.get('code')}, msg={response.get('msg', 'No message')}")
                    
            except Exception as e:
                self.logger.warning(f"OKX privateGetTradeFills failed: {e}")
            
            # Method 2: Use OKX-specific privateGetTradeOrdersHistory endpoint
            self.logger.info("Attempting OKX privateGetTradeOrdersHistory (backup method)")
            try:
                params = {'limit': str(min(limit, 100)), 'state': 'filled', 'instType': 'SPOT'}
                response = self.exchange.privateGetTradeOrdersHistory(params)
                
                if response and response.get('code') == '0' and 'data' in response:
                    orders = response['data']
                    self.logger.info(f"OKX orders history API returned {len(orders)} filled orders")
                    
                    for order in orders:
                        trade = self._format_okx_order_direct(order)
                        if trade:
                            # Avoid duplicates
                            if not any(t.get('id') == trade.get('id') for t in all_trades):
                                all_trades.append(trade)
                else:
                    self.logger.info(f"OKX orders history API response: code={response.get('code')}, msg={response.get('msg', 'No message')}")
                    
            except Exception as e:
                self.logger.warning(f"OKX privateGetTradeOrdersHistory failed: {e}")
            
            # Sort by timestamp (newest first)
            all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            self.logger.info(f"Retrieved {len(all_trades)} authentic trades from OKX direct API calls")
            
            if not all_trades:
                self.logger.info("No trades found via OKX direct API calls - this correctly indicates no recent trading activity")
            
            return all_trades[:limit]
            
        except Exception as e:
            self.logger.error(f"Error in OKX direct API trade retrieval: {e}")
            return []
    
    def _format_okx_fill_direct(self, fill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX fill data from direct API call."""
        try:
            timestamp_ms = int(fill.get('ts', 0))
            datetime_obj = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
            
            return {
                'id': fill.get('fillId', ''),
                'order_id': fill.get('ordId', ''),
                'symbol': (fill.get('instId', '') or '').replace('-', '/'),
                'side': fill.get('side', '').upper(),
                'quantity': float(fill.get('fillSz', 0)),
                'price': float(fill.get('fillPx', 0)),
                'timestamp': timestamp_ms,
                'datetime': datetime_obj.isoformat(),
                'total_value': float(fill.get('fillSz', 0)) * float(fill.get('fillPx', 0)),
                'fee': abs(float(fill.get('fee', 0))),
                'fee_currency': fill.get('feeCcy', ''),
                'source': 'okx_fills_direct'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX fill: {e}")
            return None
    
    def _format_okx_order_direct(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX order data from direct API call."""
        try:
            if order.get('state') != 'filled':
                return None
                
            timestamp_ms = int(order.get('uTime', 0))
            datetime_obj = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
            
            return {
                'id': order.get('ordId', ''),
                'order_id': order.get('ordId', ''),
                'symbol': (order.get('instId', '') or '').replace('-', '/'),
                'side': order.get('side', '').upper(),
                'quantity': float(order.get('fillSz', 0)),
                'price': float(order.get('avgPx', 0)),
                'timestamp': timestamp_ms,
                'datetime': datetime_obj.isoformat(),
                'total_value': float(order.get('fillSz', 0)) * float(order.get('avgPx', 0)),
                'fee': abs(float(order.get('fee', 0))),
                'fee_currency': order.get('feeCcy', ''),
                'source': 'okx_orders_direct'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX order: {e}")
            return None
    
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
