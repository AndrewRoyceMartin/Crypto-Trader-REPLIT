"""
State Observers
Observer pattern implementation for state change notifications
"""
from typing import Callable, Any, Dict, List, Optional
import logging
from abc import ABC, abstractmethod
from datetime import datetime

from .store import StateChange

logger = logging.getLogger(__name__)

class StateObserver(ABC):
    """Abstract base class for state observers."""
    
    @abstractmethod
    def on_state_changed(self, change: StateChange) -> None:
        """Handle state change notification."""
        pass

class LoggingObserver(StateObserver):
    """Observer that logs state changes."""
    
    def __init__(self, log_level: int = logging.DEBUG):
        self.logger = logger
        self.log_level = log_level
    
    def on_state_changed(self, change: StateChange) -> None:
        """Log state change."""
        self.logger.log(
            self.log_level,
            f"State changed: {change.path} = {change.new_value} (was: {change.old_value})"
        )

class CallbackObserver(StateObserver):
    """Observer that calls a callback function."""
    
    def __init__(self, callback: Callable[[StateChange], None]):
        self.callback = callback
    
    def on_state_changed(self, change: StateChange) -> None:
        """Call the callback function."""
        try:
            self.callback(change)
        except Exception as e:
            logger.error(f"Callback observer error: {e}")

class PathObserver(StateObserver):
    """Observer that only watches specific state paths."""
    
    def __init__(self, paths: List[str], callback: Callable[[StateChange], None]):
        self.paths = set(paths)
        self.callback = callback
    
    def on_state_changed(self, change: StateChange) -> None:
        """Handle state change if path matches."""
        if any(change.path.startswith(path) for path in self.paths):
            try:
                self.callback(change)
            except Exception as e:
                logger.error(f"Path observer error: {e}")

class PerformanceObserver(StateObserver):
    """Observer that tracks performance metrics."""
    
    def __init__(self):
        self.change_count = 0
        self.last_change = None
        self.frequent_paths: Dict[str, int] = {}
    
    def on_state_changed(self, change: StateChange) -> None:
        """Track performance metrics."""
        self.change_count += 1
        self.last_change = change.timestamp
        
        path = change.path.split('.')[0]  # Top-level path
        self.frequent_paths[path] = self.frequent_paths.get(path, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "total_changes": self.change_count,
            "last_change": self.last_change,
            "frequent_paths": self.frequent_paths
        }

# Global observer registry
_observers: List[StateObserver] = []

def add_observer(observer: StateObserver) -> None:
    """Add a global state observer."""
    if observer not in _observers:
        _observers.append(observer)

def remove_observer(observer: StateObserver) -> None:
    """Remove a global state observer."""
    if observer in _observers:
        _observers.remove(observer)

def state_changed(change: StateChange) -> None:
    """Notify all global observers of state change."""
    for observer in _observers:
        try:
            observer.on_state_changed(change)
        except Exception as e:
            logger.error(f"Observer notification failed: {e}")

# Convenience decorators
def observe_state_changes(paths: Optional[List[str]] = None):
    """Decorator to observe state changes."""
    def decorator(func: Callable[[StateChange], None]):
        if paths:
            observer = PathObserver(paths, func)
        else:
            observer = CallbackObserver(func)
        add_observer(observer)
        return func
    return decorator

def log_state_changes(log_level: int = logging.DEBUG):
    """Decorator to log state changes."""
    def decorator(cls):
        observer = LoggingObserver(log_level)
        add_observer(observer)
        return cls
    return decorator