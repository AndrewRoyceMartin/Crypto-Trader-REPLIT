"""
Enhanced trading implementation with crash protection and advanced risk management.
Integrates the advanced buy/sell logic with peak tracking and dynamic rebuy mechanisms.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, TypedDict, cast

import pandas as pd

from ..strategies.enhanced_bollinger_strategy import EnhancedBollingerBandsStrategy
from ..data.manager import DataManager
from ..risk.manager import RiskManager
from ..exchanges.base import BaseExchange
from ..config import Config


class TradeRecord(TypedDict, total=False):
    timestamp: datetime
    symbol: str
    action: str
    size: float
    price: float
    confidence: float
    event_type: str
    stop_loss: Optional[float]
    take_profit: Optional[float]
    equity_after: float
    pnl: float


class EnhancedTrader:
    """Enhanced trader with crash protection and advanced risk management."""

    def __init__(self, config: Config, exchange: BaseExchange) -> None:
        self.config = config
        self.exchange = exchange
        self.logger = logging.getLogger(__name__)

        self.data_manager = DataManager(exchange, cache_enabled=True)
        self.risk_manager = RiskManager(config)

        # Always use Enhanced Bollinger Bands Strategy
        self.strategy = EnhancedBollingerBandsStrategy(config)
        self.logger.info("Using Enhanced Bollinger Bands Strategy with crash protection")

        self.running: bool = False
        self.trade_history: List[TradeRecord] = []
        self.equity: float = config.get_float('backtesting', 'initial_capital', 10000.0)

        # Defensive defaults for position state
        self.position_state: Dict[str, Any] = (
            self.strategy.get_position_state()  # type: ignore[attr-defined]
            if hasattr(self.strategy, 'get_position_state') else
            {
                'position_qty': 0.0,
                'entry_price': 0.0,
                'peak_since_entry': 0.0,
                'rebuy_armed': False,
                'rebuy_price': 0.0,
                'rebuy_ready_at': None,
            }
        )
        self.last_update_time: Optional[datetime] = None

    def _sync_with_portfolio(self, symbol: str) -> None:
        """Sync trader position state with actual OKX portfolio holdings."""
        try:
            # Import here to avoid circular imports
            from ..services.portfolio_service import get_portfolio_service
            
            portfolio_service = get_portfolio_service()
            portfolio_data = portfolio_service.get_portfolio_data()
            holdings = portfolio_data.get('holdings', [])
            
            # Extract base symbol (e.g., SOL from SOL/USDT)
            base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
            
            # Find matching position in portfolio
            matching_position = None
            for holding in holdings:
                holding_symbol = holding.get('symbol', '')
                if holding_symbol == base_symbol:
                    matching_position = holding
                    break
            
            if matching_position:
                quantity = float(matching_position.get('quantity', 0) or 0)
                avg_entry_price = float(matching_position.get('avg_entry_price', 0) or 0)
                current_price = float(matching_position.get('current_price', 0) or 0)
                
                # Only sync if we have valid data and a real position
                if quantity > 0 and avg_entry_price > 0:
                    # Update strategy position state
                    if hasattr(self.strategy, 'position_state'):
                        self.strategy.position_state['position_qty'] = quantity
                        self.strategy.position_state['entry_price'] = avg_entry_price
                        self.strategy.position_state['peak_since_entry'] = max(avg_entry_price, current_price)
                        self.strategy.position_state['rebuy_armed'] = False  # Reset rebuy for existing positions
                        
                        self.logger.critical(
                            "🔄 PORTFOLIO SYNC: %s position found - Qty: %.8f, Entry: $%.4f, Current: $%.4f",
                            base_symbol, quantity, avg_entry_price, current_price
                        )
                        
                        # Check if position should exit immediately
                        gain_percent = ((current_price - avg_entry_price) / avg_entry_price) * 100
                        if gain_percent >= 4.0:  # Above 4% primary target
                            self.logger.warning(
                                "⚠️ EXISTING POSITION ABOVE TARGET: %s at +%.2f%% (Target: 4.0%%) - Will exit on next signal",
                                base_symbol, gain_percent
                            )
                        elif gain_percent >= 6.0:  # Above 6% safety net
                            self.logger.error(
                                "🚨 EXISTING POSITION ABOVE SAFETY NET: %s at +%.2f%% (Safety: 6.0%%) - Will exit immediately",
                                base_symbol, gain_percent
                            )
                else:
                    self.logger.info("📊 PORTFOLIO SYNC: %s - No significant position found", base_symbol)
            else:
                self.logger.info("📊 PORTFOLIO SYNC: %s - Symbol not found in portfolio", base_symbol)
                
        except Exception as e:
            self.logger.error("Failed to sync with portfolio for %s: %s", symbol, e)
            # Continue trading even if sync fails - don't break the system

    def start_trading(self, symbol: str, timeframe: str = '1h') -> None:
        self.logger.info("Starting enhanced trading: %s on %s", symbol, timeframe)
        try:
            if not self.exchange.connect():
                raise RuntimeError("Failed to connect to exchange")

            # CRITICAL: Sync with existing OKX positions before starting
            self._sync_with_portfolio(symbol)

            self.running = True

            while self.running:
                try:
                    data = self._safe_get_ohlcv(symbol, timeframe, limit=100)
                    if data is None or data.empty:
                        self.logger.warning("No data available, waiting...")
                        time.sleep(60)
                        continue

                    if "close" not in data.columns:
                        self.logger.warning("Missing 'close' column in OHLCV; waiting...")
                        time.sleep(60)
                        continue

                    current_price = float(data["close"].iloc[-1])
                    current_time = datetime.now(timezone.utc)

                    # Optional equity update without static-typing complaints
                    update_fn = getattr(self.strategy, 'update_equity', None)
                    if callable(update_fn):
                        update_fn(self.equity)

                    if not self.risk_manager.check_trading_allowed(self.equity):
                        self.logger.warning("Trading halted due to risk limits")
                        time.sleep(300)
                        continue

                    signals: Sequence[Any] = []
                    try:
                        signals = cast(Sequence[Any], self.strategy.generate_signals(data))
                    except Exception as gen_err:
                        self.logger.exception("Error generating signals: %s", gen_err)
                        time.sleep(self._get_sleep_duration(timeframe))
                        continue

                    for signal in signals:
                        if self._validate_enhanced_signal(signal):
                            self._execute_enhanced_signal(signal, symbol, current_price, current_time)

                    last_row = cast(pd.Series, data.iloc[-1])
                    self._monitor_enhanced_positions(symbol, current_price, last_row)
                    self._log_enhanced_status(symbol, current_price, current_time)

                    self.last_update_time = current_time
                    time.sleep(self._get_sleep_duration(timeframe))

                except KeyboardInterrupt:
                    self.logger.info("Trading interrupted by user")
                    break
                except Exception as loop_err:
                    self.logger.exception("Error in trading loop: %s", loop_err)
                    time.sleep(60)

        except Exception as e:
            self.logger.exception("Enhanced trading failed: %s", e)
        finally:
            self.running = False
            self.logger.info("Enhanced trading stopped")

    def stop_trading(self) -> None:
        self.running = False
        self.logger.info("Enhanced trading stop requested")

    def _safe_get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        try:
            df = self.data_manager.get_ohlcv(symbol, timeframe, limit=limit)
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)  # type: ignore[arg-type]
            return df
        except Exception as e:
            self.logger.exception("Failed to fetch OHLCV for %s %s: %s", symbol, timeframe, e)
            return None

    def _validate_enhanced_signal(self, signal: Any) -> bool:
        # Basic validate if available
        val_fn = getattr(self.strategy, 'validate_signal', None)
        if callable(val_fn):
            try:
                if not val_fn(signal):
                    return False
            except Exception:
                self.logger.debug("validate_signal failed; rejecting signal defensively")
                return False

        confidence = float(getattr(signal, "confidence", 0.0))
        size = float(getattr(signal, "size", 0.0))
        action = str(getattr(signal, "action", "")).lower()

        if confidence < 0.65:
            self.logger.debug("Signal confidence below threshold: %.2f", confidence)
            return False

        if size > 0.08:
            self.logger.warning("Position size too large: %.2f", size)
            return False

        if hasattr(self.strategy, 'get_position_state'):
            try:
                position_state = self.strategy.get_position_state()  # type: ignore[attr-defined]
            except Exception:
                position_state = {}
            if action == 'buy' and position_state.get('rebuy_armed', False):
                if not self._validate_rebuy_timing(position_state):
                    return False

        return True

    def _validate_rebuy_timing(self, position_state: Dict[str, Any]) -> bool:
        ready = position_state.get('rebuy_ready_at')
        if not ready:
            return True

        try:
            if isinstance(ready, str):
                ready_dt = datetime.fromisoformat(ready.replace('Z', '+00:00'))
            elif isinstance(ready, datetime):
                ready_dt = ready
            else:
                return False

            if ready_dt.tzinfo is None:
                ready_dt = ready_dt.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) < ready_dt:
                self.logger.debug("Rebuy cooldown not elapsed (ready at %s)", ready_dt.isoformat())
                return False

            return True
        except Exception as e:
            self.logger.warning("Error validating rebuy timing: %s", e)
            return False

    def _execute_enhanced_signal(
        self, signal: Any, symbol: str, current_price: float, timestamp: datetime
    ) -> None:
        try:
            size_pct = float(getattr(signal, "size", 0.0))
            confidence = float(getattr(signal, "confidence", 0.0))
            action = str(getattr(signal, "action", "")).lower()
            metadata = getattr(signal, "metadata", {}) or {}
            stop_loss = getattr(signal, "stop_loss", None)
            take_profit = getattr(signal, "take_profit", None)
            event_type = str(metadata.get("event", "UNKNOWN"))

            if current_price <= 0:
                return

            position_size_dollars = max(0.0, size_pct * self.equity)
            position_size_units = position_size_dollars / current_price

            if action == 'buy':
                fees = position_size_dollars * 0.001
                total_cost = position_size_dollars + fees
                if total_cost <= self.equity and position_size_units > 0:
                    self.equity -= total_cost
                    record: TradeRecord = {
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'action': 'buy',
                        'size': position_size_units,
                        'price': current_price,
                        'confidence': confidence,
                        'event_type': event_type,
                        'stop_loss': float(stop_loss) if stop_loss is not None else None,
                        'take_profit': float(take_profit) if take_profit is not None else None,
                        'equity_after': self.equity,
                    }
                    self.trade_history.append(record)
                    self.logger.info(
                        "[%s] BUY %.6f %s @ $%.2f (Conf: %.2f, Equity: $%.2f)",
                        event_type, position_size_units, symbol, current_price, confidence, self.equity
                    )

            elif action == 'sell':
                pnl_val = float(metadata.get('pnl', 0.0))
                sale_proceeds = position_size_units * current_price
                fees = sale_proceeds * 0.001
                net_proceeds = sale_proceeds - fees
                if position_size_units > 0:
                    self.equity += net_proceeds
                    record2: TradeRecord = {
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'action': 'sell',
                        'size': position_size_units,
                        'price': current_price,
                        'confidence': confidence,
                        'event_type': event_type,
                        'pnl': pnl_val,
                        'equity_after': self.equity,
                    }
                    self.trade_history.append(record2)
                    self.logger.info(
                        "[%s] SELL %.6f %s @ $%.2f (PnL: $%.2f, Equity: $%.2f)",
                        event_type, position_size_units, symbol, current_price, pnl_val, self.equity
                    )

        except Exception as e:
            self.logger.exception("Failed to execute enhanced signal: %s", e)

    def _monitor_enhanced_positions(self, symbol: str, current_price: float, current_data: pd.Series) -> None:
        if not hasattr(self.strategy, 'get_position_state'):
            return

        try:
            position_state = self.strategy.get_position_state()  # type: ignore[attr-defined]
        except Exception:
            return

        pos_qty = float(position_state.get('position_qty', 0.0) or 0.0)
        if pos_qty > 0.0:
            entry_price = float(position_state.get('entry_price', 0.0) or 0.0)
            peak_since_entry = float(position_state.get('peak_since_entry', 0.0) or 0.0)
            if entry_price > 0:
                unrealized_pnl = (current_price - entry_price) / entry_price * 100.0
                peak_dd = (peak_since_entry - current_price) / peak_since_entry * 100.0 if peak_since_entry > 0 else 0.0
                self.logger.debug(
                    "Position monitoring: Price=$%.2f, Entry=$%.2f, Peak=$%.2f, Unrealized PnL=%.2f%%, Peak DD=%.2f%%",
                    current_price, entry_price, peak_since_entry, unrealized_pnl, peak_dd
                )

        if bool(position_state.get('rebuy_armed', False)):
            rebuy_price = float(position_state.get('rebuy_price', 0.0) or 0.0)
            ready_raw = position_state.get('rebuy_ready_at')
            ready_dt: Optional[datetime] = None
            if isinstance(ready_raw, str):
                try:
                    ready_dt = datetime.fromisoformat(ready_raw.replace('Z', '+00:00'))
                except Exception:
                    ready_dt = None
            elif isinstance(ready_raw, datetime):
                ready_dt = ready_raw

            if ready_dt is not None and ready_dt.tzinfo is None:
                ready_dt = ready_dt.replace(tzinfo=timezone.utc)

            status = "READY" if (ready_dt is not None and datetime.now(timezone.utc) >= ready_dt) else "COOLDOWN"
            self.logger.debug("Rebuy armed: Price=$%.2f, Status=%s", rebuy_price, status)

    def _log_enhanced_status(self, symbol: str, current_price: float, timestamp: datetime) -> None:
        pos_qty = 0.0
        rebuy = "DISARMED"
        if hasattr(self.strategy, 'get_position_state'):
            try:
                ps = self.strategy.get_position_state()  # type: ignore[attr-defined]
                pos_qty = float(ps.get('position_qty', 0.0) or 0.0)
                rebuy = "ARMED" if ps.get('rebuy_armed', False) else "DISARMED"
            except Exception:
                pass

        parts = [
            "Enhanced Trading Status",
            f"Symbol: {symbol}",
            f"Price: ${current_price:.2f}",
            f"Equity: ${self.equity:.2f}",
            f"Position: {pos_qty:.6f}" if pos_qty > 0.0 else "Position: FLAT",
            f"Rebuy: {rebuy}",
        ]
        self.logger.info(" | ".join(parts))

    def _get_sleep_duration(self, timeframe: str) -> int:
        timeframe_map: Dict[str, int] = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400,
        }
        return timeframe_map.get(timeframe, 3600)

    def get_trading_statistics(self) -> Dict[str, Any]:
        if not self.trade_history:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'crash_exits': 0,
                'rebuy_trades': 0,
                'normal_exits': 0,
                'total_pnl': 0.0,
                'current_equity': self.equity,
                'position_state': self.position_state.copy(),
                'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            }

        trades_df = pd.DataFrame(self.trade_history)

        # Safe column extraction as Series
        if 'action' in trades_df.columns:
            action_series = trades_df['action'].astype(str)
        else:
            action_series = pd.Series(dtype='str')

        if 'event_type' in trades_df.columns:
            event_series = trades_df['event_type'].astype(str)
        else:
            event_series = pd.Series(dtype='str')

        total_trades = int(len(trades_df))
        buy_trades = int(((action_series == 'buy').astype(int)).sum())
        sell_trades = int(((action_series == 'sell').astype(int)).sum())

        crash_exits = int(((event_series == 'CRASH_EXIT').astype(int)).sum())
        rebuy_trades = int((event_series.str.contains('REBUY', na=False).astype(int)).sum())
        normal_exits = int(((event_series == 'NORMAL_EXIT').astype(int)).sum())

        total_pnl = 0.0
        if 'pnl' in trades_df.columns:
            pnl_series = pd.to_numeric(trades_df['pnl'], errors='coerce')
            # Ensure it's a Series for static type-checkers before fillna
            if isinstance(pnl_series, pd.Series):
                pnl_series = pnl_series.fillna(0.0)
                total_pnl = float(pnl_series.sum())

        # Defensive copy of position state
        position_state: Dict[str, Any] = {}
        if hasattr(self.strategy, 'get_position_state'):
            try:
                position_state = dict(self.strategy.get_position_state())  # type: ignore[attr-defined]
            except Exception:
                position_state = {}

        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'crash_exits': crash_exits,
            'rebuy_trades': rebuy_trades,
            'normal_exits': normal_exits,
            'total_pnl': total_pnl,
            'current_equity': self.equity,
            'position_state': position_state,
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
        }

    def emergency_stop(self) -> None:
        self.logger.critical("Enhanced emergency stop activated")
        if hasattr(self.strategy, 'get_position_state'):
            try:
                ps = self.strategy.get_position_state()  # type: ignore[attr-defined]
                ps.update({
                    'position_qty': 0.0,
                    'entry_price': 0.0,
                    'peak_since_entry': 0.0,
                    'rebuy_armed': False,
                    'rebuy_price': 0.0,
                    'rebuy_ready_at': None,
                })
            except Exception:
                pass
        self.stop_trading()
        self.logger.critical("Enhanced emergency stop completed")
