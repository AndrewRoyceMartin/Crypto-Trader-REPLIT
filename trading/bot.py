"""
Trading Bot Module
Handles bot state management and trading logic using business services
"""
from typing import Dict, Any, Optional
import threading
import time
import logging

logger = logging.getLogger(__name__)

# Bot state management
_state_lock = threading.RLock()
bot_state: Dict[str, Any] = {"running": False}
warmup: Dict[str, Any] = {"done": False, "error": ""}

# Initialize trading business service
_trading_business_service = None

def get_trading_business_service():
    """Get trading business service instance."""
    global _trading_business_service
    if _trading_business_service is None:
        from services.trading_business_service import TradingBusinessService
        _trading_business_service = TradingBusinessService()
    return _trading_business_service

def get_bot_status() -> Dict[str, Any]:
    """Get current bot status with runtime stats."""
    try:
        with _state_lock:
            state_copy = bot_state.copy()
        
        # Use business service for runtime calculations
        business_service = get_trading_business_service()
        runtime_stats = business_service.get_bot_runtime_stats(state_copy)
        
        running = runtime_stats["running"]
        mode = (
            state_copy.get("mode") or (
                "stopped" if not running else "unknown"
            )
        )
        
        return {
            "running": running,
            "mode": mode,
            "runtime_seconds": runtime_stats["runtime_seconds"],
            "runtime_human": runtime_stats["runtime_human"],
            "state": {
                "start_time": state_copy.get("started_at") if running else None
            }
        }
    except Exception as e:
        logger.error(f"Bot status error: {e}")
        return {
            "running": False,
            "mode": "error",
            "runtime_seconds": 0,
            "runtime_human": "0s",
            "state": {}
        }

def calculate_entry_confidence(symbol: str, current_price: float, bb_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate entry confidence using business service."""
    try:
        business_service = get_trading_business_service()
        return business_service.calculate_entry_confidence(symbol, current_price, bb_analysis)
    except Exception as e:
        logger.error(f"Entry confidence calculation failed: {e}")
        return {
            "level": "FAIR",
            "score": 50.0,
            "timing_signal": "WAIT"
        }

def get_bot_state() -> Dict[str, Any]:
    """Get bot state dictionary."""
    with _state_lock:
        return bot_state.copy()

def is_bot_running() -> bool:
    """Check if bot is currently running."""
    return bot_state.get("running", False)

def _get_warmup_done() -> bool:
    """Get warmup done status."""
    return warmup.get("done", False)

def _get_warmup_error() -> str:
    """Get warmup error message."""
    return warmup.get("error", "")