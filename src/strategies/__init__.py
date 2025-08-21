"""
Trading strategies module.
Provides base strategy class and implementations.
"""

from .base import BaseStrategy
from .enhanced_bollinger_strategy import EnhancedBollingerBandsStrategy

__all__ = ['BaseStrategy', 'EnhancedBollingerBandsStrategy']
