"""
Kraken exchange adapter for live trading.
"""

import logging

import ccxt
import pandas as pd

from .base import BaseExchange


class KrakenAdapter(BaseExchange):
    """Kraken exchange adapter."""

    def __init__(self, config: dict):
        """
        Initialize Kraken adapter.

        Args:
            config: Exchange configuration
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Connect to Kraken exchange.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.exchange = ccxt.kraken({
                'apiKey': self.config.get('apiKey', ''),
                'secret': self.config.get('secret', ''),
                'enableRateLimit': True,
            })

            # Test connection
            self.exchange.load_markets()
            self.logger.info("Successfully connected to Kraken")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Kraken: {e!s}")
            return False

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data from Kraken.

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

            from app import with_throttle
            ohlcv = with_throttle(self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit)

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df

        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data: {e!s}")
            raise

    def get_balance(self) -> dict:
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
            self.logger.error(f"Error fetching balance: {e!s}")
            raise

    def place_order(self, symbol: str, side: str, amount: float,
                   order_type: str = 'market', price: float | None = None) -> dict:
        """
        Place an order on Kraken.

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
            return order

        except Exception as e:
            self.logger.error(f"Error placing order: {e!s}")
            raise

    def get_open_orders(self, symbol: str | None = None) -> list[dict]:
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
            return orders

        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e!s}")
            raise

    def cancel_order(self, order_id: str, symbol: str) -> dict:
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
            return result

        except Exception as e:
            self.logger.error(f"Error cancelling order: {e!s}")
            raise

    def get_ticker(self, symbol: str) -> dict:
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
            return ticker

        except Exception as e:
            self.logger.error(f"Error fetching ticker: {e!s}")
            raise

    def format_symbol(self, symbol: str) -> str:
        """
        Format symbol for Kraken.

        Args:
            symbol: Symbol in standard format (BTC/USDT)

        Returns:
            Kraken-specific symbol format
        """
        # Kraken uses different symbol formats
        symbol_map = {
            'BTC/USDT': 'BTC/USDT',
            'ETH/USDT': 'ETH/USDT',
            'BTC/USD': 'XXBTZUSD',
            'ETH/USD': 'XETHZUSD'
        }

        return symbol_map.get(symbol, symbol)
