"""
Live trading implementation with real money.

Notes for static typing & pandas safety:
- TradeRecord.timestamp supports str | datetime; we normalize via _to_aware_utc().
- All datetime comparisons use timezone-aware UTC to avoid naive/aware mixups.
- No string .replace() is called on datetime objects.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypedDict, Union

import pandas as pd

from ..data.manager import DataManager
from ..strategies.base import BaseStrategy
from ..risk.manager import RiskManager
from ..exchanges.kraken_adapter import KrakenAdapter


class TradeRecord(TypedDict, total=False):
    timestamp: Union[datetime, str]
    symbol: str
    action: str
    size: float
    price: float
    order_id: str
    status: str
    signal_confidence: float
    pnl: float
    equity_after: float


class LiveTrader:
    """Live trading with real money."""

    def __init__(self, config: Any, strategy: BaseStrategy) -> None:
        """
        Initialize live trader.

        Args:
            config: Configuration object
            strategy: Trading strategy
        """
        self.config = config
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)

        # Initialize exchange and data manager
        exchange_config = config.get_exchange_config('kraken')
        self.exchange = KrakenAdapter(exchange_config)
        self.data_manager = DataManager(self.exchange, cache_enabled=True)

        # Initialize risk manager
        self.risk_manager = RiskManager(config)

        # Trading state
        self.orders: List[Dict[str, Any]] = []
        self.trade_history: List[TradeRecord] = []
        self.running = False

        # Safety checks
        self.max_daily_trades = 50
        self.daily_trade_count = 0
        self.last_trade_date: Optional[date] = None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _to_aware_utc(self, ts: Any) -> Optional[datetime]:
        """
        Convert a datetime or ISO string (with optional trailing 'Z') to a
        timezone-aware UTC datetime. Returns None if parsing fails.
        """
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)

        if isinstance(ts, str):
            s = ts.strip()
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            try:
                dt = datetime.fromisoformat(s)
            except ValueError:
                return None
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        return None

    def _get_sleep_duration(self, timeframe: str) -> int:
        """Get sleep duration based on timeframe."""
        timeframe_map = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400,
        }
        return timeframe_map.get(timeframe, 3600)  # Default to 1 hour

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    def start_trading(self, symbol: str, timeframe: str = '1h') -> None:
        """
        Start live trading.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
        """
        self.logger.critical("STARTING LIVE TRADING WITH REAL MONEY: %s", symbol)

        # Additional safety confirmation
        self.logger.warning("This will execute real trades with real money!")
        time.sleep(5)  # Give user time to cancel

        try:
            # Connect to exchange
            if not self.exchange.connect():
                raise RuntimeError("Failed to connect to exchange")

            # Validate account and check balance
            balance = self.exchange.get_balance()
            self.logger.info("Account balance: %s", balance)

            # Check if we have sufficient funds
            usd_balance = balance.get('free', {}).get('USD', 0.0)
            if float(usd_balance) < 100.0:  # Minimum $100
                raise RuntimeError(f"Insufficient funds: ${usd_balance}")

            self.running = True

            # Main trading loop
            while self.running:
                try:
                    # Reset daily trade count if new day
                    current_date = datetime.now().date()
                    if self.last_trade_date != current_date:
                        self.daily_trade_count = 0
                        self.last_trade_date = current_date

                    # Check daily trade limit
                    if self.daily_trade_count >= self.max_daily_trades:
                        self.logger.warning("Daily trade limit reached, waiting until tomorrow")
                        time.sleep(3600)  # Wait 1 hour
                        continue

                    # Get current market data
                    data = self.data_manager.get_ohlcv(symbol, timeframe, limit=100)

                    if data.empty:
                        self.logger.warning("No data available, skipping iteration")
                        time.sleep(60)
                        continue

                    # Defensive access to last price
                    try:
                        current_price = float(data['close'].iloc[-1])
                    except Exception:
                        self.logger.warning("Data missing 'close' price, skipping")
                        time.sleep(60)
                        continue

                    # Check risk limits
                    portfolio_value = self._get_portfolio_value()
                    
                    # Get USDT balance for risk check
                    try:
                        from ..services.portfolio_service import get_portfolio_service
                        portfolio_service = get_portfolio_service()
                        portfolio_data = portfolio_service.get_portfolio_data()
                        usdt_balance = portfolio_data.get('cash_balance', 0.0)
                    except Exception as e:
                        self.logger.warning(f"Failed to get USDT balance: {e}")
                        usdt_balance = 0.0

                    if not self.risk_manager.check_trading_allowed(portfolio_value, usdt_balance):
                        self.logger.warning("Trading halted due to risk limits")
                        time.sleep(300)  # Wait 5 minutes
                        continue

                    # Generate signals
                    signals = self.strategy.generate_signals(data)

                    # Process signals with extra caution
                    for signal in signals:
                        if self._validate_live_signal(signal, symbol, portfolio_value):
                            self._execute_live_signal(signal, symbol, current_price)

                    # Check and manage open positions
                    last_row = data.iloc[-1]  # type: ignore[assignment]
                    self._manage_open_positions(symbol, current_price, last_row)

                    # Log status
                    self._log_trading_status(symbol, current_price)

                    # Sleep until next iteration
                    sleep_duration = self._get_sleep_duration(timeframe)
                    time.sleep(sleep_duration)

                except KeyboardInterrupt:
                    self.logger.critical("Live trading interrupted by user")
                    break
                except Exception as e:
                    self.logger.error("Error in live trading loop: %s", str(e))
                    time.sleep(300)  # Wait 5 minutes before retrying

        except Exception as e:
            self.logger.critical("Live trading failed: %s", str(e))
        finally:
            self.running = False
            self.logger.critical("Live trading stopped")

    def stop_trading(self) -> None:
        """Stop live trading."""
        self.running = False
        self.logger.critical("Live trading stop requested")

    # -------------------------------------------------------------------------
    # Validation & Execution
    # -------------------------------------------------------------------------
    def _validate_live_signal(self, signal: Any, symbol: str, portfolio_value: float) -> bool:
        """
        Validate signal for live trading with extra safety checks.

        Args:
            signal: Trading signal
            symbol: Trading symbol
            portfolio_value: Current portfolio value

        Returns:
            True if signal is safe to execute
        """
        # Basic signal validation
        if not self.strategy.validate_signal(signal):
            return False

        # Risk manager validation
        if not self.risk_manager.validate_position_size(signal, portfolio_value):
            self.logger.warning("Signal rejected by risk manager")
            return False

        # Additional live trading safety checks

        # Check if signal confidence is high enough
        min_confidence = 0.7  # Require high confidence for live trading
        if getattr(signal, "confidence", 0.0) < min_confidence:
            self.logger.warning("Signal confidence too low: %.3f < %.3f", getattr(signal, "confidence", 0.0), min_confidence)
            return False

        # Check position size is reasonable - ONLY for buy signals
        # Sell signals use 'size' for quantity to sell, not position percentage
        signal_action = str(getattr(signal, "action", "")).lower()
        max_position_percent = 0.10  # Max 10% of portfolio per trade
        if signal_action == 'buy' and getattr(signal, "size", 0.0) > max_position_percent:
            self.logger.warning("Position size too large: %.3f > %.3f", getattr(signal, "size", 0.0), max_position_percent)
            return False

        # Throttle: avoid too many recent trades on the same symbol in last hour
        now_utc = datetime.now(timezone.utc)
        recent = 0
        for t in self.trade_history:
            if t.get('symbol') != symbol:
                continue
            ts_dt = self._to_aware_utc(t.get('timestamp'))
            if ts_dt and (now_utc - ts_dt) <= timedelta(hours=1):
                recent += 1
        if recent >= 3:
            self.logger.warning("Too many recent trades for %s", symbol)
            return False

        return True

    def _execute_live_signal(self, signal: Any, symbol: str, current_price: float) -> None:
        """
        Execute signal in live trading.

        Args:
            signal: Trading signal
            symbol: Trading symbol
            current_price: Current market price
        """
        try:
            portfolio_value = self._get_portfolio_value()
            position_size_units = float(
                self.strategy.calculate_position_size(signal, portfolio_value, current_price)
            )

            # Additional safety: limit position size
            max_size_usd = portfolio_value * 0.05  # Max 5% of portfolio
            max_size_units = max_size_usd / max(1e-12, current_price)
            position_size_units = min(position_size_units, max_size_units)

            # Place order on exchange
            order_type = 'market'  # Use market orders for immediate execution

            self.logger.critical(
                "PLACING LIVE ORDER: %s %.6f %s @ market price",
                getattr(signal, "action", "unknown").upper(),
                position_size_units,
                symbol,
            )

            order = self.exchange.place_order(
                symbol=symbol,
                side=getattr(signal, "action", "buy"),
                amount=position_size_units,
                order_type=order_type,
            )

            # Record order
            trade_record: TradeRecord = {
                'timestamp': datetime.now(timezone.utc),
                'symbol': symbol,
                'action': getattr(signal, "action", "buy"),
                'size': position_size_units,
                'price': current_price,
                'order_id': order.get('id', ''),
                'status': 'placed',
                'signal_confidence': float(getattr(signal, "confidence", 0.0)),
            }

            self.orders.append(order)
            self.trade_history.append(trade_record)
            self.daily_trade_count += 1

            self.logger.critical(
                "LIVE ORDER PLACED: %s - %s %.6f %s",
                order.get('id', ''),
                getattr(signal, "action", "buy").upper(),
                position_size_units,
                symbol,
            )

            # Set stop loss and take profit if specified
            if getattr(signal, "stop_loss", None) or getattr(signal, "take_profit", None):
                self._set_stop_orders(symbol, position_size_units, signal)

        except Exception as e:
            self.logger.error("Failed to execute live signal: %s", str(e))

    def _set_stop_orders(self, symbol: str, position_size: float, signal: Any) -> None:
        """Set stop loss and take profit orders."""
        try:
            if getattr(signal, "stop_loss", None):
                stop_order = self.exchange.place_order(
                    symbol=symbol,
                    side='sell' if getattr(signal, "action", "buy") == 'buy' else 'buy',
                    amount=position_size,
                    order_type='stop_loss',
                    price=float(getattr(signal, "stop_loss")),
                )
                self.logger.info("Stop loss set: %s @ %s", stop_order.get('id', ''), getattr(signal, "stop_loss"))

            if getattr(signal, "take_profit", None):
                tp_order = self.exchange.place_order(
                    symbol=symbol,
                    side='sell' if getattr(signal, "action", "buy") == 'buy' else 'buy',
                    amount=position_size,
                    order_type='take_profit',
                    price=float(getattr(signal, "take_profit")),
                )
                self.logger.info("Take profit set: %s @ %s", tp_order.get('id', ''), getattr(signal, "take_profit"))

        except Exception as e:
            self.logger.warning("Failed to set stop orders: %s", str(e))

    # -------------------------------------------------------------------------
    # Portfolio / Orders / Status
    # -------------------------------------------------------------------------
    def _manage_open_positions(self, symbol: str, current_price: float, current_data: pd.Series) -> None:
        """Manage open orders and basic position housekeeping."""
        try:
            # Check open orders
            open_orders = self.exchange.get_open_orders(symbol)

            # Example management placeholder
            for _order in open_orders:
                # Add modification/cancel logic here as needed
                pass

        except Exception as e:
            self.logger.error("Error managing positions: %s", str(e))

    def _get_portfolio_value(self) -> float:
        """Get current portfolio value (USD) - FIXED: Use OKX total if available."""
        try:
            balance = self.exchange.get_balance()
            
            # FIXED: Check if OKX provides total portfolio value directly
            if hasattr(balance, 'info') and balance.info:
                # Look for OKX total portfolio value in response
                total_equity = balance.info.get('totalEq') or balance.info.get('total_equity')
                if total_equity and float(total_equity) > 0:
                    self.logger.info(f"Using OKX total portfolio value: ${float(total_equity):.2f}")
                    return float(total_equity)

            # Fallback to manual calculation if OKX total not available
            total_value = 0.0
            free_balances: Dict[str, float] = balance.get('free', {}) or {}
            for currency, amount in free_balances.items():
                amt = float(amount)
                if currency.upper() == 'USD':
                    total_value += amt
                else:
                    # Convert to USD (best-effort) - still local calculation but necessary
                    try:
                        ticker = self.exchange.get_ticker(f"{currency}/USD")
                        last = float(ticker.get('last', 0.0))
                        if last > 0:
                            total_value += amt * last
                    except Exception:
                        # If conversion fails, skip silently
                        continue

            return float(total_value)

        except Exception as e:
            self.logger.error("Error getting portfolio value: %s", str(e))
            return 0.0

    def _log_trading_status(self, symbol: str, current_price: float) -> None:
        """Log current trading status."""
        portfolio_value = self._get_portfolio_value()
        self.logger.info(
            "LIVE TRADING STATUS - Portfolio: $%.2f | %s: $%.2f | Daily trades: %s",
            portfolio_value,
            symbol,
            current_price,
            self.daily_trade_count,
        )

    # -------------------------------------------------------------------------
    # Admin
    # -------------------------------------------------------------------------
    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get open orders."""
        try:
            return list(self.exchange.get_open_orders())
        except Exception as e:
            self.logger.error("Error getting open orders: %s", str(e))
            return []

    def cancel_all_orders(self, symbol: Optional[str] = None) -> None:
        """Cancel all open orders."""
        try:
            open_orders = self.exchange.get_open_orders(symbol)
            for order in open_orders:
                _ = self.exchange.cancel_order(order.get('id', ''), order.get('symbol', symbol))
                self.logger.info("Cancelled order: %s", order.get('id', ''))
        except Exception as e:
            self.logger.error("Error cancelling orders: %s", str(e))

    def emergency_stop(self) -> None:
        """Emergency stop - cancel all orders and close positions."""
        self.logger.critical("EMERGENCY STOP ACTIVATED")
        try:
            # Cancel all open orders
            self.cancel_all_orders()

            # Close all positions (simplified - best-effort)
            balance = self.exchange.get_balance()
            free_balances: Dict[str, float] = balance.get('free', {}) or {}

            for currency, amount in free_balances.items():
                if currency.upper() == 'USD':
                    continue
                amt = float(amount)
                if amt <= 0.0:
                    continue
                try:
                    symbol = f"{currency}/USD"
                    self.exchange.place_order(
                        symbol=symbol,
                        side='sell',
                        amount=amt,
                        order_type='market',
                    )
                    self.logger.critical("Emergency sell: %s %s", amt, currency)
                except Exception as e:
                    self.logger.error("Failed to emergency sell %s: %s", currency, str(e))

        except Exception as e:
            self.logger.critical("Emergency stop failed: %s", str(e))
        finally:
            self.stop_trading()
