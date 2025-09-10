"""
State Type Definitions
Defines all state interfaces and enums for type safety
"""
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict


class BotStatus(Enum):
    """Bot running status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class WarmupStatus(Enum):
    """System warmup status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TradingMode(Enum):
    """Trading operation modes."""
    PAPER = "paper"
    LIVE = "live"
    SIMULATION = "simulation"
    BACKTEST = "backtest"

class ConnectionStatus(Enum):
    """Exchange connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"

# State Interfaces

class BotState(TypedDict, total=False):
    """Bot state interface."""
    status: BotStatus
    mode: TradingMode | None
    symbol: str | None
    timeframe: str | None
    started_at: datetime | None
    error_message: str | None
    runtime_seconds: int
    active_pairs: list[str]

class WarmupState(TypedDict, total=False):
    """System warmup state interface."""
    status: WarmupStatus
    started: bool
    completed: bool
    error_message: str | None
    loaded_symbols: list[str]
    start_time: datetime | None
    progress_percent: int

class TradingState(TypedDict, total=False):
    """Trading operation state interface."""
    mode: TradingMode
    active: bool
    strategy: str | None
    start_time: datetime | None
    trade_count: int
    last_signal: str | None
    performance: dict[str, Any]

class ConnectionState(TypedDict, total=False):
    """Exchange connection state interface."""
    status: ConnectionStatus
    last_ping: datetime | None
    error_count: int
    last_error: str | None
    api_calls_today: int
    rate_limit_remaining: int

class CacheState(TypedDict, total=False):
    """Cache state interface."""
    price_cache_size: int
    ohlcv_cache_size: int
    last_cleanup: datetime | None
    hit_rate_percent: float

class AppState(TypedDict, total=False):
    """Complete application state interface."""
    bot: BotState
    warmup: WarmupState
    trading: TradingState
    connection: ConnectionState
    cache: CacheState
    server_start_time: datetime
    last_update: datetime
    admin_token_configured: bool
