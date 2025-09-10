"""
State Management Package
Provides centralized state management with thread-safe operations and observer patterns
"""

from .observers import StateObserver, state_changed
from .state_types import (
    AppState,
    BotState,
    BotStatus,
    TradingMode,
    TradingState,
    WarmupState,
    WarmupStatus,
)
from .store import StateStore, get_state_store

__all__ = [
    'AppState',
    'BotState',
    'BotStatus',
    'StateObserver',
    'StateStore',
    'TradingMode',
    'TradingState',
    'WarmupState',
    'WarmupStatus',
    'get_state_store',
    'state_changed'
]
