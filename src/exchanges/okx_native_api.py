"""
Direct OKX API integration using native endpoints for trade history retrieval.
This bypasses CCXT and uses OKX's official REST API directly.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import requests


class OKXNativeAPI:
    """Direct OKX API client for authentic trade data retrieval."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # OKX API credentials
        self.api_key = os.getenv("OKX_API_KEY")
        self.secret_key = os.getenv("OKX_SECRET_KEY")
        self.passphrase = os.getenv("OKX_PASSPHRASE")

        # Regional endpoint support
        hostname = os.getenv("OKX_HOSTNAME", "www.okx.com")
        self.base_url = f"https://{hostname}"

        if not all([self.api_key, self.secret_key, self.passphrase]):
            raise ValueError("Missing OKX API credentials")

    def _get_timestamp(self) -> str:
        """Get ISO timestamp for OKX API."""
        return datetime.now(UTC).isoformat()[:-6] + 'Z'

    def _sign_request(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """Generate OKX API signature."""
        if not self.secret_key:
            raise ValueError("Secret key is required for signing")

        message = timestamp + method.upper() + request_path + body
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    def _make_request(self, method: str, endpoint: str, params: dict | None = None) -> dict:
        """Make authenticated request to OKX API."""
        timestamp = self._get_timestamp()
        request_path = endpoint

        if params and method.upper() == 'GET':
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            request_path += f"?{query_string}"

        body = json.dumps(params) if params and method.upper() == 'POST' else ''
        signature = self._sign_request(timestamp, method, endpoint, body)

        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

        url = f"{self.base_url}{request_path}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, headers=headers, data=body, timeout=30)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"OKX API request failed: {e}")
            raise

    def get_fills_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get trade fills history using OKX native API."""
        try:
            self.logger.info(f"Fetching fills history from OKX native API (limit: {limit})")

            params = {
                'limit': str(min(limit, 100))  # OKX max limit is 100
            }

            response = self._make_request('GET', '/api/v5/trade/fills-history', params)

            if response.get('code') != '0':
                self.logger.error(f"OKX API error: {response.get('msg', 'Unknown error')}")
                return []

            fills = response.get('data', [])
            self.logger.info(f"Retrieved {len(fills)} fills from OKX native API")

            formatted_trades = []
            for fill in fills:
                trade = self._format_fill(fill)
                if trade:
                    formatted_trades.append(trade)

            return formatted_trades

        except Exception as e:
            self.logger.error(f"Failed to get fills history: {e}")
            return []

    def get_orders_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get orders history using OKX native API."""
        try:
            self.logger.info(f"Fetching orders history from OKX native API (limit: {limit})")

            params = {
                'limit': str(min(limit, 100)),
                'state': 'filled'
            }

            response = self._make_request('GET', '/api/v5/trade/orders-history', params)

            if response.get('code') != '0':
                self.logger.error(f"OKX API error: {response.get('msg', 'Unknown error')}")
                return []

            orders = response.get('data', [])
            self.logger.info(f"Retrieved {len(orders)} filled orders from OKX native API")

            formatted_trades = []
            for order in orders:
                trade = self._format_order(order)
                if trade:
                    formatted_trades.append(trade)

            return formatted_trades

        except Exception as e:
            self.logger.error(f"Failed to get orders history: {e}")
            return []

    def get_trades_comprehensive(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get comprehensive trade history using multiple OKX native endpoints."""
        all_trades = []
        seen_ids = set()

        # Method 1: Get fills history (most detailed)
        fills = self.get_fills_history(limit)
        for fill in fills:
            trade_id = fill.get('id')
            if trade_id and trade_id not in seen_ids:
                all_trades.append(fill)
                seen_ids.add(trade_id)

        # Method 2: Get orders history (backup)
        orders = self.get_orders_history(limit)
        for order in orders:
            trade_id = order.get('id')
            if trade_id and trade_id not in seen_ids:
                all_trades.append(order)
                seen_ids.add(trade_id)

        # Sort by timestamp (newest first)
        all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        self.logger.info(f"Total unique trades from OKX native API: {len(all_trades)}")
        return all_trades[:limit]

    def _format_fill(self, fill: dict[str, Any]) -> dict[str, Any] | None:
        """Format OKX fill data into standard trade format."""
        try:
            # Convert OKX timestamp to our format
            timestamp_ms = int(fill.get('ts', 0))
            datetime_obj = datetime.fromtimestamp(timestamp_ms / 1000, UTC)

            return {
                'id': fill.get('fillId', ''),
                'order_id': fill.get('ordId', ''),
                'symbol': (fill.get('instId', '') or '').replace('-', '/'),
                'side': fill.get('side', '').upper(),
                'quantity': float(fill.get('fillSz', 0)),
                'price': float(fill.get('fillPx', 0)),
                'timestamp': timestamp_ms,
                'datetime': datetime_obj.isoformat(),
                # FIXED: Use OKX notional value if available, otherwise calculate
                'total_value': float(fill.get('notionalUsd') or fill.get('notional') or (float(fill.get('fillSz', 0)) * float(fill.get('fillPx', 0)))),
                'fee': abs(float(fill.get('fee', 0))),
                'fee_currency': fill.get('feeCcy', ''),
                'trade_type': 'spot',
                'source': 'okx_native_fills'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX fill: {e}")
            return None

    def _format_order(self, order: dict[str, Any]) -> dict[str, Any] | None:
        """Format OKX order data into standard trade format."""
        try:
            # Only process filled orders
            if order.get('state') != 'filled':
                return None

            # Convert OKX timestamp to our format
            timestamp_ms = int(order.get('uTime', 0))
            datetime_obj = datetime.fromtimestamp(timestamp_ms / 1000, UTC)

            return {
                'id': order.get('ordId', ''),
                'order_id': order.get('ordId', ''),
                'symbol': (order.get('instId', '') or '').replace('-', '/'),
                'side': order.get('side', '').upper(),
                'quantity': float(order.get('fillSz', 0)),
                'price': float(order.get('avgPx', 0)),
                'timestamp': timestamp_ms,
                'datetime': datetime_obj.isoformat(),
                # FIXED: Use OKX notional/cost value if available, otherwise calculate
                'total_value': float(order.get('notionalUsd') or order.get('cost') or order.get('notional') or (float(order.get('fillSz', 0)) * float(order.get('avgPx', 0)))),
                'fee': abs(float(order.get('fee', 0))),
                'fee_currency': order.get('feeCcy', ''),
                'trade_type': 'spot',
                'source': 'okx_native_orders'
            }
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Failed to format OKX order: {e}")
            return None

    def test_connection(self) -> bool:
        """Test OKX API connection."""
        try:
            response = self._make_request('GET', '/api/v5/account/balance')
            return response.get('code') == '0'
        except Exception as e:
            self.logger.error(f"OKX connection test failed: {e}")
            return False
