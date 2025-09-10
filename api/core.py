"""
Core API utilities and shared functions
"""
import logging
import os
import threading
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# State management
_state_lock = threading.RLock()
bot_state: dict[str, Any] = {"running": False}
warmup: dict[str, Any] = {"done": False, "error": ""}
trading_state: dict[str, Any] = {}
server_start_time = datetime.now(UTC)

def get_uptime_seconds() -> int:
    """Get server uptime in seconds."""
    return int((datetime.now(UTC) - server_start_time).total_seconds())

def humanize_seconds(seconds: int) -> str:
    """Convert seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def iso_utc(dt: datetime | None = None) -> str:
    """Convert datetime to ISO UTC string."""
    if dt is None:
        dt = datetime.now(UTC)
    return dt.isoformat().replace('+00:00', 'Z')

# Admin authentication
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

# Initialize authentication service
_auth_service = None

def get_auth_service():
    """Get authentication service instance."""
    global _auth_service
    if _auth_service is None:
        from services.authentication_service import AuthenticationService
        _auth_service = AuthenticationService()
    return _auth_service

def require_admin(f: Any) -> Any:
    """Decorator to require admin authentication using service."""
    auth_service = get_auth_service()
    return auth_service.require_admin_decorator()(f)

def rate_limit(max_hits: int, per_seconds: int):
    """Decorator for rate limiting using service."""
    auth_service = get_auth_service()
    return auth_service.rate_limit_decorator(max_hits, per_seconds)
