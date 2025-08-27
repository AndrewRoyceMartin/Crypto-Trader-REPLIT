"""
State Type Definitions
Defines all state interfaces and enums for type safety
"""
from typing import TypedDict, Optional, List, Any, Dict
from enum import Enum
from datetime import datetime

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
    mode: Optional[TradingMode]
    symbol: Optional[str]
    timeframe: Optional[str]
    started_at: Optional[datetime]
    error_message: Optional[str]
    runtime_seconds: int
    active_pairs: List[str]

class WarmupState(TypedDict, total=False):
    """System warmup state interface."""
    status: WarmupStatus
    started: bool
    completed: bool
    error_message: Optional[str]
    loaded_symbols: List[str]
    start_time: Optional[datetime]
    progress_percent: int

class TradingState(TypedDict, total=False):
    """Trading operation state interface."""
    mode: TradingMode
    active: bool
    strategy: Optional[str]
    start_time: Optional[datetime]
    trade_count: int
    last_signal: Optional[str]
    performance: Dict[str, Any]

class ConnectionState(TypedDict, total=False):
    """Exchange connection state interface."""
    status: ConnectionStatus
    last_ping: Optional[datetime]
    error_count: int
    last_error: Optional[str]
    api_calls_today: int
    rate_limit_remaining: int

class CacheState(TypedDict, total=False):
    """Cache state interface."""
    price_cache_size: int
    ohlcv_cache_size: int
    last_cleanup: Optional[datetime]
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