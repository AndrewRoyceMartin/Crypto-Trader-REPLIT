"""
Enhanced OKX trade retrieval methods designed specifically for OKX API compatibility.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone


class OKXTradeRetrieval:
    """OKX-specific trade retrieval methods with comprehensive API coverage."""
    
    def __init__(self, exchange, logger):
        self.exchange = exchange
        self.logger = logger
    
    def _normalize_symbol(self, s: Optional[str]) -> Optional[str]:
        """Convert standard format (BTC/USDT) to OKX instId format (BTC-USDT)."""
        return s.replace('/', '-') if s and '/' in s else s

    def _denormalize_symbol(self, s: Optional[str]) -> Optional[str]:
        """Convert OKX instId format (BTC-USDT) to standard format (BTC/USDT)."""
        return s.replace('-', '/') if s and '-' in s else s

    def _inst_type(self) -> str:
        """
        Infer instType from ccxt okx.options.defaultType.
        Maps ccxt types to OKX instType for better API compatibility.
        """
        # Get defaultType from exchange options, with safe attribute access
        default = (getattr(self.exchange, "options", {}) or {}).get("defaultType", "spot").lower()
        return {
            "spot": "SPOT",
            "margin": "MARGIN", 
            "swap": "SWAP",
            "future": "FUTURES",
            "futures": "FUTURES",
            "option": "OPTION",
        }.get(default, "SPOT")
    
    def _trade_uid(self, t: Dict[str, Any]) -> str:
        """
        Generate a stronger composite UID for trade deduplication.
        Includes source, ID, order_id, symbol, timestamp, price, and quantity
        to prevent collisions across different sources and API responses.
        """
        return "|".join([
            t.get('source', ''),
            t.get('id', '') or t.get('order_id', ''),
            t.get('order_id', ''),
            t.get('symbol', ''),
            str(t.get('timestamp', '')),
            f"{t.get('price', '')}",
            f"{t.get('quantity', '')}",
        ])
    
    def get_trades_comprehensive(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Comprehensive trade retrieval using multiple OKX API endpoints.
        
        Args:
            symbol: Trading pair symbol (e.g., 'PEPE/USDT')
            limit: Maximum number of trades to return
            
        Returns:
            List of formatted trade dictionaries
        """
        if not self.exchange:
            self.logger.warning("Exchange not initialized")
            return []
        
        all_trades = []
        dedup_set = set()
        
        # Method 1: OKX Private Trade Fills API (most accurate)
        self.logger.info("Attempting OKX private trade fills API")
        try:
            trades = self._get_okx_trade_fills(symbol, limit)
            for trade in trades:
                uid = self._trade_uid(trade)
                if uid not in dedup_set:
                    all_trades.append(trade)
                    dedup_set.add(uid)
            self.logger.info(f"Retrieved {len(trades)} trades from fills API")
        except Exception as e:
            self.logger.warning(f"OKX fills API failed: {e}")
        
        # Method 2: OKX Orders History API
        self.logger.info("Attempting OKX orders history API")
        try:
            trades = self._get_okx_orders_history(symbol, limit)
            for trade in trades:
                uid = self._trade_uid(trade)
                if uid not in dedup_set:
                    all_trades.append(trade)
                    dedup_set.add(uid)
            self.logger.info(f"Retrieved {len(trades)} trades from orders history API")
        except Exception as e:
            self.logger.warning(f"OKX orders history API failed: {e}")
        
        # Method 3: Standard CCXT methods as fallback
        self.logger.info("Attempting standard CCXT methods")
        try:
            trades = self._get_ccxt_trades(symbol, limit)
            for trade in trades:
                uid = self._trade_uid(trade)
                if uid not in dedup_set:
                    all_trades.append(trade)
                    dedup_set.add(uid)
            self.logger.info(f"Retrieved {len(trades)} trades from CCXT methods")
        except Exception as e:
            self.logger.warning(f"CCXT methods failed: {e}")
        
        # Final sort by timestamp (most recent first)
        all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        self.logger.info(f"Final result: {len(all_trades)} unique trades after enhanced deduplication")
        return all_trades[:limit]
    
    def _get_okx_trade_fills(self, symbol: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Get trades using OKX's trade fills API with enhanced instType support."""
        try:
            params = {
                'limit': str(limit),
                'instType': self._inst_type()
            }
            
            if symbol:
                params['instId'] = self._normalize_symbol(symbol)
            
            # Use OKX's private trade fills endpoint
            response = self.exchange.privateGetTradeFills(params)
            
            if not response or 'data' not in response:
                return []
            
            fills = response['data']
            trades = []
            
            for fill in fills:
                trade = self._format_okx_fill(fill)
                if trade:
                    trades.append(trade)
            
            return trades
            
        except Exception as e:
            self.logger.debug(f"OKX fills API error: {e}")
            return []
    
    def _get_okx_orders_history(self, symbol: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Get trades using OKX's orders history API with enhanced instType support."""
        try:
            params = {
                'limit': str(limit),
                'state': 'filled',  # Only filled orders
                'instType': self._inst_type()
            }
            
            if symbol:
                params['instId'] = self._normalize_symbol(symbol)
            
            # Use OKX's private orders history endpoint
            response = self.exchange.privateGetTradeOrdersHistory(params)
            
            if not response or 'data' not in response:
                return []
            
            orders = response['data']
            trades = []
            
            for order in orders:
                trade = self._format_okx_order(order)
                if trade:
                    trades.append(trade)
            
            return trades
            
        except Exception as e:
            self.logger.debug(f"OKX orders history API error: {e}")
            return []
    
    def _get_ccxt_trades(self, symbol: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Get trades using standard CCXT methods."""
        trades = []
        
        try:
            # Try fetch_my_trades
            my_trades = self.exchange.fetch_my_trades(symbol=symbol, limit=limit)
            for trade in my_trades:
                formatted = self._format_ccxt_trade(trade)
                if formatted:
                    trades.append(formatted)
        except Exception as e:
            self.logger.debug(f"fetch_my_trades failed: {e}")
        
        try:
            # Try fetch_closed_orders
            orders = self.exchange.fetch_closed_orders(symbol=symbol, limit=limit)
            for order in orders:
                if order.get('status') == 'closed' and order.get('filled', 0) > 0:
                    trade = self._format_ccxt_order_as_trade(order)
                    if trade:
                        trades.append(trade)
        except Exception as e:
            self.logger.debug(f"fetch_closed_orders failed: {e}")
        
        return trades
    
    def _format_okx_fill(self, fill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX fill data into standard trade format with enhanced timezone and fee handling."""
        try:
            ts = int(fill.get('ts', 0)) or 0
            price = float(fill.get('fillPx', 0) or 0)
            qty = float(fill.get('fillSz', 0) or 0)
            fee_raw = float(fill.get('fee', 0) or 0)

            return {
                'id': fill.get('fillId', ''),
                'order_id': fill.get('ordId', ''),
                'client_order_id': fill.get('clOrdId', '') or None,
                'symbol': self._denormalize_symbol(fill.get('instId', '') or ''),
                'inst_type': fill.get('instType', '').upper() or self._inst_type(),
                'side': (fill.get('side', '') or '').upper(),
                'quantity': qty,
                'price': price,
                'timestamp': ts,
                'datetime': datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat() if ts else '',
                'total_value': qty * price,
                'fee': abs(fee_raw),
                'fee_sign': -1 if fee_raw < 0 else (1 if fee_raw > 0 else 0),
                'fee_currency': fill.get('feeCcy', ''),
                'trade_type': 'spot' if (fill.get('instType', '').upper() or self._inst_type()) == 'SPOT' else 'derivatives',
                'source': 'okx_fills',
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX fill: {e}")
            return None
    
    def _format_okx_order(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX order data into standard trade format with enhanced timezone and fee handling."""
        try:
            if (order.get('state') or '').lower() != 'filled':
                return None

            # prefer accumulated filled size for filled orders
            qty = float(order.get('accFillSz') or order.get('fillSz') or order.get('sz') or 0)
            price = float(order.get('avgPx') or order.get('px') or 0)
            ts = int(order.get('uTime') or order.get('cTime') or 0)
            fee_raw = float(order.get('fee', 0) or 0)

            return {
                'id': order.get('ordId', ''),
                'order_id': order.get('ordId', ''),
                'client_order_id': order.get('clOrdId', '') or None,
                'symbol': self._denormalize_symbol(order.get('instId', '') or ''),
                'inst_type': order.get('instType', '').upper() or self._inst_type(),
                'side': (order.get('side', '') or '').upper(),
                'quantity': qty,
                'price': price,
                'timestamp': ts,
                'datetime': datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat() if ts else '',
                'total_value': qty * price if (qty and price) else float(order.get('notionalUsd', 0) or 0),
                'fee': abs(fee_raw),
                'fee_sign': -1 if fee_raw < 0 else (1 if fee_raw > 0 else 0),
                'fee_currency': order.get('feeCcy', ''),
                'trade_type': 'spot' if (order.get('instType', '').upper() or self._inst_type()) == 'SPOT' else 'derivatives',
                'source': 'okx_orders',
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX order: {e}")
            return None
    
    def _format_ccxt_trade(self, trade: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format CCXT trade data into standard format."""
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
                'fee': trade.get('fee', {}).get('cost', 0),
                'fee_currency': trade.get('fee', {}).get('currency', ''),
                'trade_type': 'spot',
                'source': 'ccxt_trades'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format CCXT trade: {e}")
            return None
    
    def _format_ccxt_order_as_trade(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format CCXT order data as trade with enhanced timestamp and fee handling."""
        try:
            ts = int(order.get('lastTradeTimestamp') or order.get('timestamp') or 0)
            qty = float(order.get('filled') or order.get('amount') or 0)
            price = float(order.get('average') or order.get('price') or 0)
            fee = order.get('fee') or {}
            fee_cost = float(fee.get('cost', 0) or 0)
            fee_ccy = fee.get('currency', '')
            
            return {
                'id': order.get('id', ''),
                'order_id': order.get('id', ''),
                'client_order_id': order.get('clientOrderId', '') or None,
                'symbol': order.get('symbol', ''),
                'inst_type': self._inst_type(),
                'side': (order.get('side', '') or '').upper(),
                'quantity': qty,
                'price': price,
                'timestamp': ts,
                'datetime': order.get('datetime') or (datetime.fromtimestamp(ts/1000, tz=timezone.utc).isoformat() if ts else ''),
                'total_value': float(order.get('cost') or (qty * price)),
                'fee': abs(fee_cost),
                'fee_sign': -1 if fee_cost < 0 else (1 if fee_cost > 0 else 0),
                'fee_currency': fee_ccy,
                'trade_type': 'spot' if self._inst_type() == 'SPOT' else 'derivatives',
                'source': 'ccxt_orders',
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format CCXT order: {e}")
            return None