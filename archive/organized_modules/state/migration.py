"""
State Migration Adapter
Provides backward compatibility with existing state management
"""
import contextlib
import logging
import threading
from datetime import UTC, datetime
from typing import Any

from .state_types import BotStatus, TradingMode, WarmupStatus
from .store import get_state_store

logger = logging.getLogger(__name__)

class StateMigrationAdapter:
    """Adapter to maintain backward compatibility with legacy state management."""

    def __init__(self):
        self.store = get_state_store()
        self._legacy_lock = threading.RLock()

    # Legacy bot_state compatibility
    @property
    def bot_state(self) -> dict[str, Any]:
        """Legacy bot_state dictionary interface."""
        bot_state = self.store.get_bot_state()
        return {
            "running": bot_state.get('status') == BotStatus.RUNNING,
            "mode": bot_state.get('mode').value if bot_state.get('mode') and hasattr(bot_state.get('mode'), 'value') else None,
            "symbol": bot_state.get('symbol'),
            "timeframe": bot_state.get('timeframe'),
            "started_at": bot_state.get('started_at')
        }

    # Legacy warmup compatibility
    @property
    def warmup(self) -> dict[str, Any]:
        """Legacy warmup dictionary interface."""
        warmup_state = self.store.get_warmup_state()
        return {
            "started": warmup_state.get('started', False),
            "completed": warmup_state.get('completed', False),
            "error": warmup_state.get('error_message')
        }

    # Legacy trading_state compatibility
    @property
    def trading_state(self) -> dict[str, Any]:
        """Legacy trading_state dictionary interface."""
        trading_state = self.store.get_trading_state()
        return {
            "mode": trading_state.get('mode').value if trading_state.get('mode') and hasattr(trading_state.get('mode'), 'value') else "stopped",
            "active": trading_state.get('active', False),
            "strategy": trading_state.get('strategy'),
            "start_time": trading_state.get('start_time').isoformat() if trading_state.get('start_time') and hasattr(trading_state.get('start_time'), 'isoformat') else None,
            "type": None  # Legacy field
        }

    # Thread-safe state updates (legacy interface)
    def _set_bot_state(self, **kwargs) -> None:
        """Thread-safe bot state update (legacy interface)."""
        with self._legacy_lock:
            updates = {}

            if 'running' in kwargs:
                updates['status'] = BotStatus.RUNNING if kwargs['running'] else BotStatus.STOPPED
            if kwargs.get('mode'):
                try:
                    updates['mode'] = TradingMode(kwargs['mode'])
                except ValueError:
                    logger.warning(f"Invalid trading mode: {kwargs['mode']}")
            if 'symbol' in kwargs:
                updates['symbol'] = kwargs['symbol']
            if 'timeframe' in kwargs:
                updates['timeframe'] = kwargs['timeframe']
            if 'started_at' in kwargs:
                updates['started_at'] = kwargs['started_at']

            if updates:
                self.store.set_bot_state(**updates)

    def _set_warmup(self, **kwargs) -> None:
        """Thread-safe warmup state update (legacy interface)."""
        with self._legacy_lock:
            updates = {}

            if 'started' in kwargs:
                updates['started'] = kwargs['started']
                if kwargs['started']:
                    updates['status'] = WarmupStatus.IN_PROGRESS
                    updates['start_time'] = datetime.now(UTC)
            if 'completed' in kwargs:
                updates['completed'] = kwargs['completed']
                if kwargs['completed']:
                    updates['status'] = WarmupStatus.COMPLETED
                    updates['progress_percent'] = 100
            if 'error' in kwargs:
                updates['error_message'] = kwargs['error']
                if kwargs['error']:
                    updates['status'] = WarmupStatus.FAILED

            if updates:
                self.store.set_warmup_state(**updates)

    def _set_trading_state(self, **kwargs) -> None:
        """Thread-safe trading state update (legacy interface)."""
        with self._legacy_lock:
            updates = {}

            if 'mode' in kwargs:
                if kwargs['mode'] == "stopped":
                    updates['active'] = False
                else:
                    try:
                        updates['mode'] = TradingMode(kwargs['mode'])
                        updates['active'] = True
                    except ValueError:
                        logger.warning(f"Invalid trading mode: {kwargs['mode']}")
            if 'active' in kwargs:
                updates['active'] = kwargs['active']
            if 'strategy' in kwargs:
                updates['strategy'] = kwargs['strategy']
            if 'start_time' in kwargs:
                if isinstance(kwargs['start_time'], str):
                    with contextlib.suppress(ValueError):
                        updates['start_time'] = datetime.fromisoformat(kwargs['start_time'].replace('Z', '+00:00'))
                else:
                    updates['start_time'] = kwargs['start_time']

            if updates:
                self.store.set_trading_state(**updates)

    # Legacy getter methods
    def _get_bot_running(self) -> bool:
        """Get bot running status (legacy interface)."""
        return self.store.get_state('bot.status') == BotStatus.RUNNING

    def _get_warmup_done(self) -> bool:
        """Get warmup completion status (legacy interface)."""
        return self.store.get_state('warmup.completed') or False

    def _get_warmup_error(self) -> str | None:
        """Get warmup error (legacy interface)."""
        return self.store.get_state('warmup.error_message')

# Global migration adapter instance
_migration_adapter: StateMigrationAdapter | None = None
_adapter_lock = threading.RLock()

def get_migration_adapter() -> StateMigrationAdapter:
    """Get global migration adapter instance."""
    global _migration_adapter

    with _adapter_lock:
        if _migration_adapter is None:
            _migration_adapter = StateMigrationAdapter()

        return _migration_adapter
