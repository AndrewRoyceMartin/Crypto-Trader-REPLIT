"""
Trading strategies module.
Provides base strategy class and implementations.
"""

from .base import BaseStrategy
from .bollinger_strategy import BollingerBandsStrategy

__all__ = ['BaseStrategy', 'BollingerBandsStrategy']
