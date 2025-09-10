# src/utils/safe_shims.py
from __future__ import annotations

import contextlib
from typing import Any


def safe_get_boll_target(symbol: str, current_price: float) -> dict[str, Any]:
    """
    Safe shim: try to import real function from enhanced_bollinger_strategy.
    If not available, return an empty dict (caller will fall back gracefully).
    """
    try:
        from src.strategies.enhanced_bollinger_strategy import get_bollinger_target_price as _real
        return _real(symbol, current_price)
    except Exception:
        return {}

# ---- Optional state.store shim ----
class _NullStateStore:
    def get_bot_state(self) -> dict:
        return {"status": "stopped"}
    def set_bot_state(self, **kwargs) -> None:
        # No-op; used only to quiet missing module situations
        return None

def get_state_store():
    """
    Safe shim for `state.store.get_state_store`. If real impl is importable,
    users should import that directly. This exists only to avoid ImportError
    at runtime where the store is optional.
    """
    try:
        from src.utils.safe_shims import get_state_store as get_state_store as _real
        return _real()
    except Exception:
        return _NullStateStore()

# ---- Optional adapter method guards ----
def try_clear_cache(obj: Any) -> None:
    if hasattr(obj, "clear_cache") and callable(obj.clear_cache):
        with contextlib.suppress(Exception):
            obj

def try_invalidate_cache(obj: Any) -> None:
    if hasattr(obj, "invalidate_cache") and callable(obj.invalidate_cache):
        with contextlib.suppress(Exception):
            obj

def try_fetch_my_trades(exchange: Any, symbol: str, since: int | None = None, limit: int | None = None):
    if hasattr(exchange, "fetch_my_trades") and callable(exchange.fetch_my_trades):
        return try_fetch_my_trades(exchange, symbol=symbol, since=since, limit=limit)
    return []
