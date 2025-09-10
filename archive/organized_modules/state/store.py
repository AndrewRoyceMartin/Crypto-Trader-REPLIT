"""
Centralized State Store
Thread-safe state management with observer pattern support
"""
import json
import logging
import os
import threading
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, TypeVar

from .state_types import (
    AppState,
    BotState,
    BotStatus,
    ConnectionState,
    ConnectionStatus,
    TradingMode,
    TradingState,
    WarmupState,
    WarmupStatus,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class StateChange:
    """Represents a state change event."""
    path: str
    old_value: Any
    new_value: Any
    timestamp: datetime

class StateStore:
    """Centralized thread-safe state store with observer pattern."""

    def __init__(self, persist_file: str | None = None):
        self._state: AppState = self._create_initial_state()
        self._lock = threading.RLock()
        self._observers: list[Callable[[StateChange], None]] = []
        self._persist_file = persist_file
        self._logger = logger

        # Load persisted state if available
        if self._persist_file and os.path.exists(self._persist_file):
            self._load_state()

    def _create_initial_state(self) -> AppState:
        """Create initial application state."""
        now = datetime.now(UTC)

        return {
            'bot': {
                'status': BotStatus.STOPPED,
                'mode': None,
                'symbol': None,
                'timeframe': None,
                'started_at': None,
                'error_message': None,
                'runtime_seconds': 0,
                'active_pairs': []
            },
            'warmup': {
                'status': WarmupStatus.NOT_STARTED,
                'started': False,
                'completed': False,
                'error_message': None,
                'loaded_symbols': [],
                'start_time': None,
                'progress_percent': 0
            },
            'trading': {
                'mode': TradingMode.PAPER,
                'active': False,
                'strategy': None,
                'start_time': None,
                'trade_count': 0,
                'last_signal': None,
                'performance': {}
            },
            'connection': {
                'status': ConnectionStatus.DISCONNECTED,
                'last_ping': None,
                'error_count': 0,
                'last_error': None,
                'api_calls_today': 0,
                'rate_limit_remaining': 1000
            },
            'cache': {
                'price_cache_size': 0,
                'ohlcv_cache_size': 0,
                'last_cleanup': None,
                'hit_rate_percent': 0.0
            },
            'server_start_time': now,
            'last_update': now,
            'admin_token_configured': bool(os.getenv("ADMIN_TOKEN"))
        }

    def get_state(self, path: str | None = None) -> Any:
        """Get state value by path or entire state."""
        with self._lock:
            if path is None:
                return deepcopy(self._state)

            keys = path.split('.')
            value = self._state

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None

            return deepcopy(value) if isinstance(value, dict | list) else value

    def set_state(self, path: str, value: Any) -> None:
        """Set state value by path."""
        with self._lock:
            keys = path.split('.')
            old_value = self.get_state(path)

            # Navigate to parent
            current = self._state
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the value
            final_key = keys[-1]
            current[final_key] = value

            # Update last_update timestamp
            self._state['last_update'] = datetime.now(UTC)

            # Notify observers
            change = StateChange(
                path=path,
                old_value=old_value,
                new_value=value,
                timestamp=datetime.now(UTC)
            )
            self._notify_observers(change)

            # Persist if configured
            if self._persist_file:
                self._save_state()

    def update_state(self, path: str, updates: dict[str, Any]) -> None:
        """Update multiple fields in a state section."""
        with self._lock:
            current_state = self.get_state(path) or {}
            if isinstance(current_state, dict):
                current_state.update(updates)
                self.set_state(path, current_state)
            else:
                self._logger.warning(f"Cannot update non-dict state at path: {path}")

    def get_bot_state(self) -> BotState:
        """Get bot state."""
        return self.get_state('bot') or {}

    def set_bot_state(self, **updates) -> None:
        """Update bot state."""
        self.update_state('bot', updates)

    def get_warmup_state(self) -> WarmupState:
        """Get warmup state."""
        return self.get_state('warmup') or {}

    def set_warmup_state(self, **updates) -> None:
        """Update warmup state."""
        self.update_state('warmup', updates)

    def get_trading_state(self) -> TradingState:
        """Get trading state."""
        return self.get_state('trading') or {}

    def set_trading_state(self, **updates) -> None:
        """Update trading state."""
        self.update_state('trading', updates)

    def get_connection_state(self) -> ConnectionState:
        """Get connection state."""
        return self.get_state('connection') or {}

    def set_connection_state(self, **updates) -> None:
        """Update connection state."""
        self.update_state('connection', updates)

    def add_observer(self, observer: Callable[[StateChange], None]) -> None:
        """Add state change observer."""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def remove_observer(self, observer: Callable[[StateChange], None]) -> None:
        """Remove state change observer."""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def _notify_observers(self, change: StateChange) -> None:
        """Notify all observers of state change."""
        for observer in self._observers:
            try:
                observer(change)
            except Exception as e:
                self._logger.error(f"Observer notification failed: {e}")

    def _save_state(self) -> None:
        """Save state to persistent storage."""
        if not self._persist_file:
            return

        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serializable_state = self._make_serializable(deepcopy(self._state))

            with open(self._persist_file, 'w') as f:
                json.dump(serializable_state, f, indent=2)

        except Exception as e:
            self._logger.error(f"Failed to save state: {e}")

    def _load_state(self) -> None:
        """Load state from persistent storage."""
        if not self._persist_file or not os.path.exists(self._persist_file):
            return

        try:
            with open(self._persist_file) as f:
                stored_state = json.load(f)

            # Convert ISO strings back to datetime objects
            self._state = self._restore_from_serializable(stored_state)

        except Exception as e:
            self._logger.error(f"Failed to load state: {e}")

    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'value'):
            return obj.value
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj

    def _restore_from_serializable(self, obj: Any) -> Any:
        """Restore object from JSON-serializable format."""
        if isinstance(obj, str):
            # Try to parse as datetime
            try:
                return datetime.fromisoformat(obj.replace('Z', '+00:00'))
            except ValueError:
                return obj
        elif isinstance(obj, dict):
            return {k: self._restore_from_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._restore_from_serializable(item) for item in obj]
        else:
            return obj

    def reset_state(self) -> None:
        """Reset to initial state."""
        with self._lock:
            self._state = self._create_initial_state()
            if self._persist_file:
                self._save_state()

# Global state store instance
_state_store: StateStore | None = None
_store_lock = threading.RLock()

def get_state_store() -> StateStore:
    """Get global state store instance."""
    global _state_store

    with _store_lock:
        if _state_store is None:
            # Use persistent storage in development
            persist_file = os.path.join(os.getcwd(), '.state.json') if os.getenv('REPLIT_DB_URL') else None
            _state_store = StateStore(persist_file=persist_file)

        return _state_store
