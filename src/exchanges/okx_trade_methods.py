"""
Enhanced OKX trade retrieval methods designed specifically for OKX API compatibility.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class OKXTradeRetrieval:
    """OKX-specific trade retrieval methods with comprehensive API coverage."""
    
    def __init__(self, exchange, logger):
        self.exchange = exchange
        self.logger = logger
    
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
                trade_key = f"{trade.get('id', '')}{trade.get('timestamp', '')}{trade.get('symbol', '')}"
                if trade_key not in dedup_set:
                    all_trades.append(trade)
                    dedup_set.add(trade_key)
            self.logger.info(f"Retrieved {len(trades)} trades from fills API")
        except Exception as e:
            self.logger.warning(f"OKX fills API failed: {e}")
        
        # Method 2: OKX Orders History API
        self.logger.info("Attempting OKX orders history API")
        try:
            trades = self._get_okx_orders_history(symbol, limit)
            for trade in trades:
                trade_key = f"{trade.get('id', '')}{trade.get('timestamp', '')}{trade.get('symbol', '')}"
                if trade_key not in dedup_set:
                    all_trades.append(trade)
                    dedup_set.add(trade_key)
            self.logger.info(f"Retrieved {len(trades)} trades from orders history API")
        except Exception as e:
            self.logger.warning(f"OKX orders history API failed: {e}")
        
        # Method 3: Standard CCXT methods as fallback
        self.logger.info("Attempting standard CCXT methods")
        try:
            trades = self._get_ccxt_trades(symbol, limit)
            for trade in trades:
                trade_key = f"{trade.get('id', '')}{trade.get('timestamp', '')}{trade.get('symbol', '')}"
                if trade_key not in dedup_set:
                    all_trades.append(trade)
                    dedup_set.add(trade_key)
            self.logger.info(f"Retrieved {len(trades)} trades from CCXT methods")
        except Exception as e:
            self.logger.warning(f"CCXT methods failed: {e}")
        
        # Remove duplicates and sort
        unique_trades = []
        seen_keys = set()
        for trade in all_trades:
            key = f"{trade.get('id', '')}{trade.get('symbol', '')}{trade.get('timestamp', '')}"
            if key not in seen_keys:
                unique_trades.append(trade)
                seen_keys.add(key)
        
        unique_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        self.logger.info(f"Final result: {len(unique_trades)} unique trades")
        return unique_trades[:limit]
    
    def _get_okx_trade_fills(self, symbol: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Get trades using OKX's trade fills API."""
        try:
            params = {
                'limit': str(limit)
            }
            
            if symbol:
                # Convert PEPE/USDT -> PEPE-USDT for OKX
                okx_symbol = symbol.replace('/', '-') if '/' in symbol else symbol
                params['instId'] = okx_symbol
            
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
        """Get trades using OKX's orders history API."""
        try:
            params = {
                'limit': str(limit),
                'state': 'filled'  # Only filled orders
            }
            
            if symbol:
                okx_symbol = symbol.replace('/', '-') if '/' in symbol else symbol
                params['instId'] = okx_symbol
            
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
        """Format OKX fill data into standard trade format."""
        try:
            return {
                'id': fill.get('fillId', ''),
                'order_id': fill.get('ordId', ''),
                'symbol': (fill.get('instId', '') or '').replace('-', '/'),
                'side': fill.get('side', '').upper(),
                'quantity': float(fill.get('fillSz', 0)),
                'price': float(fill.get('fillPx', 0)),
                'timestamp': int(fill.get('ts', 0)),
                'datetime': datetime.fromtimestamp(int(fill.get('ts', 0)) / 1000).isoformat() if fill.get('ts') else '',
                'total_value': float(fill.get('fillSz', 0)) * float(fill.get('fillPx', 0)),
                'fee': float(fill.get('fee', 0)),
                'fee_currency': fill.get('feeCcy', ''),
                'trade_type': 'spot',
                'source': 'okx_fills'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX fill: {e}")
            return None
    
    def _format_okx_order(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format OKX order data into standard trade format."""
        try:
            if order.get('state') != 'filled':
                return None
                
            return {
                'id': order.get('ordId', ''),
                'order_id': order.get('ordId', ''),
                'symbol': (order.get('instId', '') or '').replace('-', '/'),
                'side': order.get('side', '').upper(),
                'quantity': float(order.get('fillSz', 0)),
                'price': float(order.get('avgPx', 0)),
                'timestamp': int(order.get('uTime', 0)),
                'datetime': datetime.fromtimestamp(int(order.get('uTime', 0)) / 1000).isoformat() if order.get('uTime') else '',
                'total_value': float(order.get('fillSz', 0)) * float(order.get('avgPx', 0)),
                'fee': float(order.get('fee', 0)),
                'fee_currency': order.get('feeCcy', ''),
                'trade_type': 'spot',
                'source': 'okx_orders'
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
        """Format CCXT order data as trade."""
        try:
            return {
                'id': order.get('id', ''),
                'order_id': order.get('id', ''),
                'symbol': order.get('symbol', ''),
                'side': (order.get('side', '') or '').upper(),
                'quantity': float(order.get('filled', 0)),
                'price': float(order.get('average', 0)),
                'timestamp': int(order.get('timestamp', 0)),
                'datetime': order.get('datetime', ''),
                'total_value': float(order.get('cost', 0)),
                'fee': order.get('fee', {}).get('cost', 0) if order.get('fee') else 0,
                'fee_currency': order.get('fee', {}).get('currency', '') if order.get('fee') else '',
                'trade_type': 'spot',
                'source': 'ccxt_orders'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format CCXT order: {e}")
            return None