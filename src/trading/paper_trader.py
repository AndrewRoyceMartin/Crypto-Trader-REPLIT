"""
Paper trading implementation.
Simulates trading without real money.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

from ..data.manager import DataManager
from ..exchanges.okx_adapter import OKXAdapter
from ..risk.manager import RiskManager
from ..strategies.base import BaseStrategy


class PaperTrader:
    """Paper trading simulation class."""

    def __init__(self, config: Any, strategy: BaseStrategy) -> None:
        """
        Initialize paper trader.

        Args:
            config: Configuration object
            strategy: Trading strategy
        """
        self.config = config
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)

        # Initialize exchange and data manager
        exchange_config = config.get_exchange_config("okx_demo")
        self.exchange = OKXAdapter(exchange_config)
        self.data_manager = DataManager(self.exchange, cache_enabled=True)

        # Initialize risk manager
        self.risk_manager = RiskManager(config)

        # Paper trading state
        self.initial_capital: float = float(
            config.get_float("backtesting", "initial_capital", 10000.0)
        )
        self.cash: float = self.initial_capital
        # symbol -> position dict
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: List[Dict[str, Any]] = []
        self.trade_history: List[Dict[str, Any]] = []

        # Trading parameters
        self.commission: float = float(config.get_float("backtesting", "commission", 0.001))
        self.slippage: float = float(config.get_float("backtesting", "slippage", 0.0005))

        self.running: bool = False

    def start_trading(self, symbol: str, timeframe: str = "1h") -> None:
        """
        Start paper trading.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
        """
        self.logger.info("Starting paper trading: %s", symbol)

        try:
            # Connect to exchange
            if not self.exchange.connect():
                raise RuntimeError("Failed to connect to exchange")

            self.running = True

            # Main trading loop
            while self.running:
                try:
                    # Get current market data
                    data = self.data_manager.get_ohlcv(symbol, timeframe, limit=100)

                    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
                        self.logger.warning("No data available, skipping iteration")
                        time.sleep(60)
                        continue

                    # Validate expected columns to avoid pandas KeyErrors
                    for col in ("open", "high", "low", "close"):
                        if col not in data.columns:
                            self.logger.warning("Missing column '%s' in OHLCV; skipping", col)
                            time.sleep(60)
                            continue

                    current_price = float(data["close"].iloc[-1])
                    current_time = datetime.now(timezone.utc)

                    # Check risk limits
                    portfolio_value = self.get_portfolio_value()
                    if not self.risk_manager.check_trading_allowed(portfolio_value):
                        self.logger.warning("Trading halted due to risk limits")
                        time.sleep(300)  # Wait 5 minutes
                        continue

                    # Generate signals
                    signals = self.strategy.generate_signals(data)

                    # Process signals
                    for signal in signals:
                        if self.strategy.validate_signal(signal):
                            if self.risk_manager.validate_position_size(signal, portfolio_value):
                                self._execute_signal(signal, symbol, current_price, current_time)

                    # Check exit conditions for open positions
                    self._check_exit_conditions(symbol, current_price, data.iloc[-1])

                    # Log portfolio status
                    self._log_portfolio_status(symbol, current_price)

                    # Sleep until next iteration
                    sleep_duration = self._get_sleep_duration(timeframe)
                    time.sleep(sleep_duration)

                except KeyboardInterrupt:
                    self.logger.info("Paper trading interrupted by user")
                    break
                except Exception as e:
                    self.logger.error("Error in trading loop: %s", e)
                    time.sleep(60)  # Wait 1 minute before retrying

        except Exception as e:
            self.logger.error("Paper trading failed: %s", e)
        finally:
            self.running = False
            self.logger.info("Paper trading stopped")

    def stop_trading(self) -> None:
        """Stop paper trading."""
        self.running = False
        self.logger.info("Paper trading stop requested")

    def _execute_signal(
        self, signal: Any, symbol: str, current_price: float, timestamp: datetime
    ) -> None:
        """
        Execute a trading signal.

        Args:
            signal: Trading signal
            symbol: Trading symbol
            current_price: Current market price
            timestamp: Execution timestamp
        """
        try:
            # Calculate position size
            portfolio_value = self.get_portfolio_value()
            raw_size = self.strategy.calculate_position_size(signal, portfolio_value, current_price)
            position_size = float(raw_size or 0.0)
            if position_size <= 0.0:
                return

            # Apply slippage
            execution_price = (
                current_price * (1 + self.slippage)
                if str(signal.action).lower() == "buy"
                else current_price * (1 - self.slippage)
            )

            # Calculate costs
            trade_value = position_size * execution_price
            commission_cost = trade_value * self.commission
            total_cost = trade_value + commission_cost

            # Execute trade
            action = str(signal.action).lower()
            if action == "buy":
                # Check if we have enough cash
                if total_cost > self.cash + 1e-12:
                    self.logger.warning(
                        "Insufficient cash for buy order: $%.2f > $%.2f", total_cost, self.cash
                    )
                    return
                self._execute_buy(
                    symbol,
                    position_size,
                    execution_price,
                    commission_cost,
                    timestamp,
                    signal,
                )
            elif action == "sell":
                self._execute_sell(
                    symbol,
                    position_size,
                    execution_price,
                    commission_cost,
                    timestamp,
                    signal,
                )

        except Exception as e:
            self.logger.error("Error executing signal: %s", e)

    def _execute_buy(
        self,
        symbol: str,
        size: float,
        price: float,
        commission: float,
        timestamp: datetime,
        signal: Any,
    ) -> None:
        """Execute buy order."""
        if size <= 0.0:
            return

        trade_value = size * price
        total_cost = trade_value + commission

        # Update cash
        self.cash -= total_cost

        # Update position
        pos = self.positions.get(symbol)
        if pos is None:
            pos = {
                "size": 0.0,
                "avg_price": 0.0,
                "unrealized_pnl": 0.0,
                "stop_loss": None,
                "take_profit": None,
            }
            self.positions[symbol] = pos

        prev_size = float(pos["size"])
        prev_avg = float(pos["avg_price"])

        new_total_size = prev_size + size
        if new_total_size > 0.0:
            pos["avg_price"] = (prev_size * prev_avg + size * price) / new_total_size
        pos["size"] = new_total_size
        pos["stop_loss"] = getattr(signal, "stop_loss", None)
        pos["take_profit"] = getattr(signal, "take_profit", None)

        # Record trade
        trade: Dict[str, Any] = {
            "timestamp": timestamp,
            "symbol": symbol,
            "action": "buy",
            "size": size,
            "price": price,
            "commission": commission,
            "total_cost": total_cost,
        }
        self.trade_history.append(trade)
        self.logger.info(
            "Executed BUY: %.6f %s @ $%.2f (Commission: $%.2f)", size, symbol, price, commission
        )

    def _execute_sell(
        self,
        symbol: str,
        size: float,
        price: float,
        commission: float,
        timestamp: datetime,
        signal: Any,
    ) -> None:
        """Execute sell order."""
        if size <= 0.0:
            return

        pos = self.positions.get(symbol)
        if pos is None or float(pos.get("size", 0.0)) <= 0.0:
            self.logger.warning("No position to sell for %s", symbol)
            return

        current_pos_size = float(pos["size"])
        sell_size = min(size, current_pos_size)

        trade_value = sell_size * price
        net_proceeds = trade_value - commission

        # Calculate realized P&L
        avg_price = float(pos.get("avg_price", 0.0))
        realized_pnl = sell_size * (price - avg_price)

        # Update cash
        self.cash += net_proceeds

        # Update position
        remaining = current_pos_size - sell_size
        if remaining > 0.0:
            pos["size"] = remaining
            # keep avg_price as cost basis for remaining
        else:
            # Close position completely
            self.positions.pop(symbol, None)

        # Record trade
        trade: Dict[str, Any] = {
            "timestamp": timestamp,
            "symbol": symbol,
            "action": "sell",
            "size": sell_size,
            "price": price,
            "commission": commission,
            "net_proceeds": net_proceeds,
            "realized_pnl": realized_pnl,
        }
        self.trade_history.append(trade)
        self.logger.info(
            "Executed SELL: %.6f %s @ $%.2f (P&L: $%.2f)", sell_size, symbol, price, realized_pnl
        )

    def _check_exit_conditions(
        self, symbol: str, current_price: float, current_data: pd.Series
    ) -> None:
        """Check if any positions should be exited."""
        pos = self.positions.get(symbol)
        if pos is None:
            return

        strategy_position: Dict[str, Any] = {
            "side": "long",
            "size": float(pos["size"]),
            "entry_price": float(pos["avg_price"]),
            "stop_loss": pos.get("stop_loss"),
            "take_profit": pos.get("take_profit"),
        }

        exit_signal = self.strategy.should_exit_position(
            strategy_position, current_price, current_data
        )
        if exit_signal:
            timestamp = datetime.now(timezone.utc)
            commission = float(pos["size"]) * current_price * self.commission
            self._execute_sell(
                symbol, float(pos["size"]), current_price, commission, timestamp, exit_signal
            )

    def _log_portfolio_status(self, symbol: str, current_price: float) -> None:
        """Log current portfolio status."""
        portfolio_value = self.get_portfolio_value()
        total_return_pct = (
            (portfolio_value - self.initial_capital) / self.initial_capital * 100.0
            if self.initial_capital > 0
            else 0.0
        )

        position_info = ""
        pos = self.positions.get(symbol)
        if pos:
            size = float(pos["size"])
            avg_price = float(pos["avg_price"])
            unrealized_pnl = size * (current_price - avg_price)
            position_info = f" | Position: {size:.6f} @ ${avg_price:.2f} (P&L: ${unrealized_pnl:.2f})"

        self.logger.info(
            "Portfolio: $%.2f (%+.2f%%) | Cash: $%.2f%s",
            portfolio_value,
            total_return_pct,
            self.cash,
            position_info,
        )

    def _get_sleep_duration(self, timeframe: str) -> int:
        """Get sleep duration based on timeframe."""
        tf = timeframe.strip().lower()
        timeframe_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
        }
        return int(timeframe_map.get(tf, 3600))  # Default to 1 hour

    def get_portfolio_value(self) -> float:
        """
        Calculate current portfolio value.

        Returns:
            Total portfolio value
        """
        total_value = float(self.cash)

        # Add position values (use current prices)
        for sym, pos in self.positions.items():
            try:
                ticker = self.exchange.get_ticker(sym)
                # be defensive: last may be None or string
                last_raw = ticker.get("last")
                last = float(last_raw) if last_raw is not None else float(ticker.get("close", 0.0))
                if last <= 0.0:
                    continue
                size = float(pos.get("size", 0.0))
                total_value += size * last
            except Exception as e:
                self.logger.warning("Could not get current price for %s: %s", sym, e)

        return total_value

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions (copy to avoid external mutation)."""
        return {k: dict(v) for k, v in self.positions.items()}

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history (copy to avoid external mutation)."""
        return [dict(t) for t in self.trade_history]

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.

        Returns:
            Performance summary dictionary
        """
        portfolio_value = self.get_portfolio_value()
        total_return = (
            (portfolio_value - self.initial_capital) / self.initial_capital
            if self.initial_capital > 0
            else 0.0
        )

        # Calculate trade statistics
        total_trades = len(self.trade_history)
        profitable_trades = sum(
            1 for trade in self.trade_history if float(trade.get("realized_pnl", 0.0)) > 0.0
        )
        win_rate = (profitable_trades / total_trades) if total_trades > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "current_value": portfolio_value,
            "total_return": total_return,
            "cash": self.cash,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "positions": len(self.positions),
        }
