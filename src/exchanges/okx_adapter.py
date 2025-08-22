"""
OKX exchange adapter for live trading.
"""

import ccxt
import pandas as pd
import logging
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from ccxt.base.errors import BaseError, NetworkError, ExchangeError, RateLimitExceeded
from .base import BaseExchange


class OKXAdapter(BaseExchange):
    """OKX exchange adapter for live trading."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OKX adapter with configuration."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.exchange: Optional[ccxt.okx] = None
        self._is_connected = False
    
    def _retry(self, fn, *args, max_attempts: int = 3, base_delay: float = 0.5, **kwargs) -> Any:
        """Retry helper with exponential backoff for network errors and rate limits."""
        for i in range(max_attempts):
            try:
                return fn(*args, **kwargs)
            except (RateLimitExceeded, NetworkError) as e:
                # Increase delay for rate limit errors to reduce API pressure
                wait = base_delay * (3 ** i)  # More aggressive backoff for OKX rate limits
                self.logger.debug(f"{fn.__name__} retry {i+1}/{max_attempts} after {e}, sleeping {wait:.2f}s")
                time.sleep(wait)
            except (ExchangeError, BaseError):
                raise  # Don't retry on authentication/permission errors
        # Final attempt without retry
        return fn(*args, **kwargs)

    def _build_client(self, default_type: str = 'spot') -> ccxt.okx:
        """Build OKX client with centralized configuration and explicit demo mode control."""
        api_key = os.getenv("OKX_API_KEY") or self.config.get("apiKey", "")
        secret = os.getenv("OKX_API_SECRET") or os.getenv("OKX_SECRET_KEY") or self.config.get("secret", "")
        passphrase = os.getenv("OKX_API_PASSPHRASE") or os.getenv("OKX_PASSPHRASE") or self.config.get("password", "")
        hostname = os.getenv("OKX_HOSTNAME") or os.getenv("OKX_REGION") or "www.okx.com"
        
        # Explicit demo mode control - production defaults to live trading
        is_demo = os.getenv("OKX_SIMULATED", "0") == "1"
        
        if not all([api_key, secret, passphrase]):
            raise RuntimeError("Missing OKX API credentials (OKX_API_KEY/OKX_API_SECRET/OKX_API_PASSPHRASE)")

        # Build exchange instance - production defaults to live trading
        ex = ccxt.okx({
            'apiKey': api_key,
            'secret': secret,
            'password': passphrase,
            'hostname': hostname,
            'sandbox': False,  # Never use sandbox - production defaults to live trading
            'enableRateLimit': True,
            'timeout': 30000,
            'options': {
                'defaultType': default_type,
                # 'fetchMyTradesMethod': 'privateGetTradeFillsHistory'  # optional
            }
        })
        
        # Apply simulated trading header only if explicitly requested via environment
        if is_demo:
            self.logger.warning("OKX_SIMULATED=1 detected - enabling simulated trading mode")
            ex.headers = {
                **getattr(ex, "headers", {}), 
                "x-simulated-trading": "1"
            }
        else:
            self.logger.info("Using live OKX trading mode (production default)")
        
        ex.load_markets()
        return ex

    def connect(self) -> bool:
        """Connect to OKX exchange using centralized client builder."""
        try:
            self.exchange = self._build_client(default_type='spot')
            self.logger.info("Connected to OKX (live spot)")
            self._is_connected = True
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to connect to OKX: {error_msg}")
            
            # Provide specific guidance for common OKX errors
            if "50119" in error_msg:
                self.logger.error("OKX Error 50119: API key doesn't exist. This usually means:")
                self.logger.error("1. API key was created for demo/testnet but connecting to live trading")
                self.logger.error("2. API key lacks required permissions (need Read + Trade)")
                self.logger.error("3. IP address not whitelisted")
                self.logger.error("4. API key was disabled or incorrectly copied")
                self.logger.error("5. FOR AUSTRALIA: ASIC-compliant verification not completed")
                self.logger.error("See OKX_API_SETUP_GUIDE.md for detailed fix instructions")
            elif "50011" in error_msg:
                self.logger.error("OKX Error 50011: Request timestamp expired. Fix:")
                self.logger.error("1. Check system time is synchronized (NTP)")
                self.logger.error("2. Verify timezone settings are correct")
                self.logger.error("3. Network latency may be causing delays")
            elif "50117" in error_msg or "50126" in error_msg:
                self.logger.error(f"OKX Error {error_msg.split()[1] if len(error_msg.split()) > 1 else 'Permission'}: Insufficient permissions. Fix:")
                self.logger.error("1. API key missing required permissions (need Read + Trade)")
                self.logger.error("2. Check API key restrictions in OKX console")
                self.logger.error("3. Verify trading permissions are enabled")
            elif "50125" in error_msg:
                self.logger.error("OKX Error 50125: IP address not whitelisted. Fix:")
                self.logger.error("1. Add current IP to API key whitelist in OKX console")
                self.logger.error("2. Check if using VPN - may need VPN IP whitelisted")
                self.logger.error("3. Wait 5 minutes after IP whitelist changes")
            
            self._is_connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to exchange."""
        return self._is_connected and self.exchange is not None
    
    def get_balance(self) -> Dict[str, Any]:
        """Get account balance with robust retry logic."""
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            balance = self._retry(self.exchange.fetch_balance)
            
            # Validate balance response
            if not isinstance(balance, dict):
                raise ValueError("Invalid balance response format")
            
            # Log balance summary for debugging (demoted from info to reduce noise)
            total_assets = len([k for k, v in balance.get('total', {}).items() if v > 0])
            self.logger.debug(f"Balance retrieved: {total_assets} assets with non-zero balance")
            
            return balance
                    
        except (NetworkError, ExchangeError, BaseError) as e:
            self.logger.error(f"Failed to fetch balance: {e}")
            raise
        except (ValueError, TypeError) as e:
            self.logger.error(f"Balance validation error: {e}")
            raise
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get open positions. For spot: derive from balances; for derivatives: use fetch_positions().
        Correctly handles spot trading by building positions from balance data.
        """
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")

        try:
            default_type = (getattr(self.exchange, 'options', {}) or {}).get('defaultType', 'spot')
            if default_type == 'spot':
                # For spot trading, build positions from balance data
                bal = self._retry(self.exchange.fetch_balance)
                details = bal.get('info', {}).get('data', [{}])[0].get('details', []) or []
                positions = []
                
                for d in details:
                    ccy = d.get('ccy')
                    total = float(d.get('bal', 0) or 0)
                    avail = float(d.get('availBal', 0) or 0)
                    if total > 0:
                        positions.append({
                            'symbol': f"{ccy}/USDT" if ccy and ccy != 'USDT' else 'USDT/USDT',
                            'asset': ccy,
                            'quantity': total,
                            'available': avail,
                            'type': 'spot',
                        })
                
                self.logger.info(f"Retrieved {len(positions)} spot positions from OKX balance data")
                return positions
            else:
                # For derivatives trading, use standard fetch_positions
                pos = self._retry(self.exchange.fetch_positions)
                derivative_positions = [dict(p) for p in pos if float(p.get('contracts', 0) or 0) > 0]
                self.logger.info(f"Retrieved {len(derivative_positions)} derivative positions from OKX")
                return derivative_positions
                
        except Exception as e:
            self.logger.error(f"Error fetching positions: {e}")
            raise
    
    def place_order(self, symbol: str, side: str, amount: float, order_type: str = "market", price: Optional[float] = None) -> Dict[str, Any]:
        """Place an order on the exchange with retry logic."""
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            if order_type == "market":
                order = self._retry(self.exchange.create_market_order, symbol, side, amount)
            elif order_type == "limit" and price is not None:
                order = self._retry(self.exchange.create_limit_order, symbol, side, amount, price)
            else:
                raise ValueError("Invalid order type or missing price for limit order")
            
            return dict(order)
        except (NetworkError, ExchangeError, BaseError) as e:
            self.logger.error(f"Error placing order: {e}")
            raise
        except ValueError as e:
            self.logger.error(f"Order validation error: {e}")
            raise
    
    def get_trades(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get trade history using comprehensive OKX API endpoints.
        Prioritizes OKX-specific endpoints for maximum accuracy and coverage.
        """
        if not self.is_connected() or self.exchange is None:
            self.logger.warning("Not connected to OKX exchange")
            return []
        
        try:
            all_trades = []
            seen_trade_ids = set()
            
            # Method 1: OKX Trade Fills API (most comprehensive for executed trades)
            try:
                fills_params = {
                    'limit': str(min(limit, 100)),  # OKX max 100
                    'instType': 'SPOT'  # Focus on spot trading
                }
                if symbol:
                    fills_params['instId'] = self.denormalize_symbol(symbol)
                
                self.logger.debug(f"Fetching trade fills from OKX API with params: {fills_params}")
                response = self._retry(self.exchange.privateGetTradeFills, fills_params)
                
                if self._is_okx_success_response(response):
                    fills = response['data']
                    self.logger.debug(f"OKX fills API returned {len(fills)} trade fills")
                    
                    for fill in fills:
                        trade = self._format_okx_fill_direct(fill)
                        if trade and trade['id'] not in seen_trade_ids:
                            all_trades.append(trade)
                            seen_trade_ids.add(trade['id'])
                else:
                    self.logger.debug(f"OKX fills API response: {response.get('code')} - {response.get('msg', 'No message')}")
                    
            except Exception as e:
                self.logger.warning(f"OKX privateGetTradeFills failed: {e}")
            
            # Method 2: OKX Orders History API (backup for different data coverage)
            try:
                orders_params = {
                    'limit': str(min(limit, 100)),
                    'state': 'filled',
                    'instType': 'SPOT'
                }
                if symbol:
                    orders_params['instId'] = self.denormalize_symbol(symbol)
                
                self.logger.debug(f"Fetching order history from OKX API with params: {orders_params}")
                response = self._retry(self.exchange.privateGetTradeOrdersHistory, orders_params)
                
                if self._is_okx_success_response(response):
                    orders = response['data']
                    self.logger.debug(f"OKX orders API returned {len(orders)} filled orders")
                    
                    for order in orders:
                        trade = self._format_okx_order_direct(order)
                        if trade and trade['id'] not in seen_trade_ids:
                            all_trades.append(trade)
                            seen_trade_ids.add(trade['id'])
                else:
                    self.logger.debug(f"OKX orders API response: {response.get('code')} - {response.get('msg', 'No message')}")
                    
            except Exception as e:
                self.logger.warning(f"OKX privateGetTradeOrdersHistory failed: {e}")
            
            # Method 3: Enhanced CCXT fallback for broader coverage
            if len(all_trades) == 0:
                self.logger.info("No trades from OKX direct APIs, attempting CCXT fallback methods")
                fallback_trades = self._get_ccxt_trades_enhanced(symbol, limit)
                for trade in fallback_trades:
                    if trade.get('id') not in seen_trade_ids:
                        all_trades.append(trade)
                        seen_trade_ids.add(trade['id'])
            
            # Sort by timestamp (newest first) and apply limit
            all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            result_trades = all_trades[:limit]
            
            self.logger.debug(f"Successfully retrieved {len(result_trades)} unique trades from OKX APIs")
            
            if not result_trades:
                self.logger.debug("No trades found - this indicates no recent trading activity on the account")
            
            return result_trades
            
        except Exception as e:
            self.logger.error(f"Critical error in OKX trade retrieval: {e}")
            return []
    
    def _is_okx_success_response(self, response: Dict[str, Any]) -> bool:
        """Check if OKX API response indicates success."""
        if not response:
            return False
        return (response.get('code') == '0' and 
                'data' in response and 
                isinstance(response['data'], list))
    
    def _get_ccxt_trades_enhanced(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Enhanced CCXT fallback method with multiple approaches."""
        fallback_trades = []
        
        if self.exchange is None:
            return fallback_trades
            
        try:
            # CCXT Method 1: fetch_my_trades
            self.logger.debug("Attempting CCXT fetch_my_trades")
            ccxt_trades = self._retry(self.exchange.fetch_my_trades, symbol=symbol, limit=min(limit, 100))
            for trade in ccxt_trades:
                formatted = self._format_ccxt_trade(trade)
                if formatted:
                    fallback_trades.append(formatted)
                    
        except Exception as e:
            self.logger.debug(f"CCXT fetch_my_trades failed: {e}")
        
        try:
            # CCXT Method 2: fetch_closed_orders (converted to trades)
            self.logger.debug("Attempting CCXT fetch_closed_orders")
            closed_orders = self._retry(self.exchange.fetch_closed_orders, symbol=symbol, limit=min(limit, 100))
            for order in closed_orders:
                if order.get('status') == 'closed' and order.get('filled', 0) > 0:
                    formatted = self._format_ccxt_order_as_trade(order)
                    if formatted:
                        fallback_trades.append(formatted)
                        
        except Exception as e:
            self.logger.debug(f"CCXT fetch_closed_orders failed: {e}")
        
        return fallback_trades
    
    def _format_ccxt_trade(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format CCXT trade data to match our standard format."""
        try:
            return {
                'id': trade.get('id', ''),
                'order_id': trade.get('order', ''),
                'symbol': trade.get('symbol', ''),
                'side': (trade.get('side', '') or '').upper(),
                'quantity': float(trade.get('amount', 0)),
                'price': float(trade.get('price', 0)),
                'timestamp': int(trade.get('timestamp', 0)),
                'datetime': trade.get('datetime', ''),
                'total_value': float(trade.get('cost', 0)),
                'fee': trade.get('fee', {}).get('cost', 0) if trade.get('fee') else 0,
                'fee_currency': trade.get('fee', {}).get('currency', '') if trade.get('fee') else '',
                'source': 'ccxt_trades'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format CCXT trade: {e}")
            return None
    
    def _format_ccxt_order_as_trade(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format CCXT order data as trade data."""
        try:
            return {
                'id': order.get('id', ''),
                'order_id': order.get('id', ''),
                'symbol': order.get('symbol', ''),
                'side': (order.get('side', '') or '').upper(),
                'quantity': float(order.get('filled', 0)),
                'price': float(order.get('average', 0)) if order.get('average') else float(order.get('price', 0)),
                'timestamp': int(order.get('timestamp', 0)),
                'datetime': order.get('datetime', ''),
                'total_value': float(order.get('cost', 0)),
                'fee': order.get('fee', {}).get('cost', 0) if order.get('fee') else 0,
                'fee_currency': order.get('fee', {}).get('currency', '') if order.get('fee') else '',
                'source': 'ccxt_orders'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format CCXT order: {e}")
            return None
    
    def _format_okx_fill_direct(self, fill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX fill data from direct API call with enhanced validation."""
        try:
            # Validate required fields
            if not fill.get('fillId') or not fill.get('instId'):
                self.logger.debug(f"OKX fill missing required fields: {fill}")
                return None
            
            timestamp_ms = int(fill.get('ts', 0))
            if timestamp_ms == 0:
                self.logger.debug("OKX fill has invalid timestamp")
                return None
                
            datetime_obj = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
            
            # Calculate values with proper error handling
            quantity = float(fill.get('fillSz', 0))
            price = float(fill.get('fillPx', 0))
            
            # FIXED: Use OKX notional/USD value if available, otherwise calculate
            okx_notional = fill.get('notionalUsd') or fill.get('notional')
            if okx_notional and float(okx_notional) > 0:
                total_value = float(okx_notional)
                self.logger.debug(f"Using OKX notional value for fill: ${total_value:.2f}")
            else:
                total_value = quantity * price if quantity and price else 0
            
            return {
                'id': fill.get('fillId', ''),
                'order_id': fill.get('ordId', ''),
                'symbol': (fill.get('instId', '') or '').replace('-', '/'),
                'side': fill.get('side', '').upper(),
                'quantity': quantity,
                'price': price,
                'timestamp': timestamp_ms,
                'datetime': datetime_obj.isoformat(),
                'total_value': total_value,
                'fee': abs(float(fill.get('fee', 0))),
                'fee_currency': fill.get('feeCcy', ''),
                'trade_type': fill.get('instType', 'SPOT').lower(),
                'source': 'okx_fills'
            }
        except (ValueError, TypeError, OverflowError) as e:
            self.logger.debug(f"Failed to format OKX fill {fill.get('fillId', 'unknown')}: {e}")
            return None
    
    def _format_okx_order_direct(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX order data from direct API call with enhanced validation."""
        try:
            # Only process filled orders
            if order.get('state') != 'filled':
                return None
            
            # Validate required fields
            if not order.get('ordId') or not order.get('instId'):
                self.logger.debug(f"OKX order missing required fields: {order}")
                return None
                
            timestamp_ms = int(order.get('uTime', 0))
            if timestamp_ms == 0:
                self.logger.debug("OKX order has invalid timestamp")
                return None
                
            datetime_obj = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
            
            # Calculate values with proper validation
            quantity = float(order.get('fillSz', 0))
            price = float(order.get('avgPx', 0))
            total_value = quantity * price if quantity and price else 0
            
            return {
                'id': order.get('ordId', ''),
                'order_id': order.get('ordId', ''),
                'symbol': (order.get('instId', '') or '').replace('-', '/'),
                'side': order.get('side', '').upper(),
                'quantity': quantity,
                'price': price,
                'timestamp': timestamp_ms,
                'datetime': datetime_obj.isoformat(),
                'total_value': total_value,
                'fee': abs(float(order.get('fee', 0))),
                'fee_currency': order.get('feeCcy', ''),
                'order_type': order.get('ordType', 'market'),
                'trade_type': order.get('instType', 'SPOT').lower(),
                'source': 'okx_orders'
            }
        except (ValueError, TypeError, OverflowError) as e:
            self.logger.debug(f"Failed to format OKX order {order.get('ordId', 'unknown')}: {e}")
            return None
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get order book for a symbol."""
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            order_book = self._retry(self.exchange.fetch_order_book, symbol, limit)
            return dict(order_book)
        except Exception as e:
            self.logger.error(f"Error fetching order book for {symbol}: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for a symbol with retry logic."""
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            ticker = self._retry(self.exchange.fetch_ticker, symbol)
            return dict(ticker)
        except (NetworkError, ExchangeError, BaseError) as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise
    
    def get_exchange_rates(self) -> dict:
        """Alias for get_currency_conversion_rates for compatibility."""
        return self.get_currency_conversion_rates()
    
    def get_currency_conversion_rates(self) -> dict:
        """
        Return conversion FROM USD into {USD, EUR, GBP, AUD}.
        Since USDT ≈ USD, use fiat/USDT and invert to get USD->FIAT.
        """
        if not self.is_connected() or self.exchange is None:
            self.logger.warning("Exchange not connected, cannot get currency rates")
            return {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "AUD": 1.52}

        pairs = {"EUR": "EUR/USDT", "GBP": "GBP/USDT", "AUD": "AUD/USDT"}
        rates = {"USD": 1.0}
        for cur, pair in pairs.items():
            try:
                t = self._retry(self.exchange.fetch_ticker, pair)
                last = float(t.get('last') or 0.0)  # USDT per 1 FIAT
                # USD->FIAT ≈ 1 / (USDT per FIAT)
                rates[cur] = (1.0 / last) if last > 0 else rates.get(cur, 1.0)
            except Exception as e:
                self.logger.warning(f"Rate fallback for {cur}: {e}")
                # sensible fallback
                fallback = {"EUR": 0.92, "GBP": 0.79, "AUD": 1.52}
                rates[cur] = fallback[cur]
        self.logger.info(f"USD->FIAT conversion rates: {rates}")
        return rates
    
    def _legacy_get_trades_fallback(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fallback trade retrieval method using basic OKX API calls."""
        if self.exchange is None:
            return []
            
        all_trades = []
        
        # Method 1: Try fetch_my_trades (standard method)
        try:
            self.logger.info(f"Attempting fetch_my_trades with limit={limit}")
            if symbol:
                trades = self._retry(self.exchange.fetch_my_trades, symbol, limit=min(limit, 50))
            else:
                trades = self._retry(self.exchange.fetch_my_trades, limit=min(limit, 100))
            
            self.logger.info(f"fetch_my_trades returned {len(trades)} trades")
            all_trades.extend([dict(trade) for trade in trades])
            
        except Exception as e:
            self.logger.warning(f"fetch_my_trades failed: {str(e)}")
        
        # Method 2: Try fetch_closed_orders (OKX specific method)
        try:
            self.logger.info("Attempting fetch_closed_orders (OKX-specific method)")
            closed_orders = self._retry(self.exchange.fetch_closed_orders, limit=min(limit, 100))
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
                symbol_orders = self._retry(self.exchange.fetch_closed_orders, symbol_check, limit=20)
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
            self.logger.info("Attempting fetch_closed_orders with time range (last 7 days)")
            
            recent_orders = self._retry(self.exchange.fetch_closed_orders, since=since, limit=min(limit, 200))
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
        
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        all_trades = []
        
        # Method 1: Try fetch_my_trades with since parameter
        try:
            self.logger.info(f"Attempting fetch_my_trades with timeframe={timeframe}, since={since}")
            trades = self._retry(self.exchange.fetch_my_trades, since=since, limit=min(limit, 100))
            self.logger.info(f"fetch_my_trades returned {len(trades)} trades for timeframe {timeframe}")
            all_trades.extend([dict(trade) for trade in trades])
        except Exception as e:
            self.logger.warning(f"fetch_my_trades with timeframe failed: {str(e)}")
        
        # Method 2: Try fetch_closed_orders with since parameter
        try:
            self.logger.info(f"Attempting fetch_closed_orders with timeframe={timeframe}")
            closed_orders = self._retry(self.exchange.fetch_closed_orders, since=since, limit=min(limit, 100))
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
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            ohlcv = self._retry(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv)
            if len(df.columns) >= 6:
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {str(e)}")
            raise
    

    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            orders = self._retry(self.exchange.fetch_open_orders, symbol)
            return [dict(order) for order in orders]
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {str(e)}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order with retry logic."""
        if not self.is_connected() or self.exchange is None:
            raise RuntimeError("Not connected to exchange")
        
        try:
            result = self._retry(self.exchange.cancel_order, order_id, symbol)
            return dict(result)
        except (NetworkError, ExchangeError, BaseError) as e:
            self.logger.error(f"Error canceling order: {e}")
            raise
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get order history (alias for get_trades)."""
        return self.get_trades(symbol, limit)
    
    # Symbol normalization helpers
    def normalize_symbol(self, s: str) -> str:
        """Convert OKX instId format (BTC-USDT) to standard format (BTC/USDT)."""
        return (s or '').replace('-', '/')
    
    def denormalize_symbol(self, s: str) -> str:
        """Convert standard format (BTC/USDT) to OKX instId format (BTC-USDT)."""
        return (s or '').replace('/', '-')
    
    def healthcheck(self) -> bool:
        """Quick connectivity and permissions verification."""
        if self.exchange is None:
            return False
        try:
            self._retry(self.exchange.load_markets)
            self._retry(self.exchange.fetch_balance)
            return True
        except Exception as e:
            self.logger.error(f"Healthcheck failed: {e}")
            return False




def make_okx_spot() -> ccxt.okx:
    """
    Factory function for OKX spot client - delegates to centralized builder.
    Returns authenticated OKX client ready for live spot trading.
    """
    # Use centralized client builder
    return OKXAdapter({'apiKey': '', 'secret': '', 'password': ''})._build_client('spot')
