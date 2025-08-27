"""
Trading Bot Module
Handles bot state management and trading logic
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

def get_bot_status() -> Dict[str, Any]:
    """Get current bot status."""
    with _state_lock:
        running = bool(bot_state.get("running", False))
        trading_state = {}
        
        mode = (
            bot_state.get("mode") or (
                "stopped" if not running else trading_state.get("mode")
            )
        )
        trading_state["start_time"] = bot_state.get("started_at") if running else None
        
        return {
            "running": running,
            "mode": mode,
            "state": trading_state
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