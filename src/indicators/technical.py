"""
Technical indicators implementation.
Provides Bollinger Bands, ATR, and other technical indicators.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple


class TechnicalIndicators:
    """Technical indicators calculation class."""
    
    def __init__(self):
        """Initialize technical indicators."""
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            data: Price data (typically close prices)
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        try:
            # Calculate moving average (middle band)
            middle_band = data.rolling(window=period).mean()
            
            # Calculate standard deviation
            std = data.rolling(window=period).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)
            
            return upper_band, middle_band, lower_band
            
        except Exception as e:
            raise Exception(f"Error calculating Bollinger Bands: {str(e)}")
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR).
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period
            
        Returns:
            ATR values
        """
        try:
            # Calculate True Range components
            hl = high - low
            hc = abs(high - close.shift())
            lc = abs(low - close.shift())
            
            # True Range is the maximum of the three
            tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
            
            # Calculate ATR as exponential moving average of TR
            atr = tr.ewm(span=period).mean()
            
            return atr
            
        except Exception as e:
            raise Exception(f"Error calculating ATR: {str(e)}")
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            data: Price data
            period: RSI period
            
        Returns:
            RSI values
        """
        try:
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            raise Exception(f"Error calculating RSI: {str(e)}")
    
    @staticmethod
    def macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            data: Price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        try:
            # Calculate EMAs
            ema_fast = data.ewm(span=fast_period).mean()
            ema_slow = data.ewm(span=slow_period).mean()
            
            # Calculate MACD line
            macd_line = ema_fast - ema_slow
            
            # Calculate signal line
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # Calculate histogram
            histogram = macd_line - signal_line
            
            return macd_line, signal_line, histogram
            
        except Exception as e:
            raise Exception(f"Error calculating MACD: {str(e)}")
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.
        
        Args:
            data: Price data
            period: Moving average period
            
        Returns:
            SMA values
        """
        try:
            return data.rolling(window=period).mean()
        except Exception as e:
            raise Exception(f"Error calculating SMA: {str(e)}")
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: Price data
            period: EMA period
            
        Returns:
            EMA values
        """
        try:
            return data.ewm(span=period).mean()
        except Exception as e:
            raise Exception(f"Error calculating EMA: {str(e)}")
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                  k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: %K period
            d_period: %D period
            
        Returns:
            Tuple of (%K, %D)
        """
        try:
            # Calculate %K
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            
            # Calculate %D (SMA of %K)
            d_percent = k_percent.rolling(window=d_period).mean()
            
            return k_percent, d_percent
            
        except Exception as e:
            raise Exception(f"Error calculating Stochastic: {str(e)}")
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Williams %R.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Williams %R period
            
        Returns:
            Williams %R values
        """
        try:
            highest_high = high.rolling(window=period).max()
            lowest_low = low.rolling(window=period).min()
            
            williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
            
            return williams_r
            
        except Exception as e:
            raise Exception(f"Error calculating Williams %R: {str(e)}")
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).
        
        Args:
            close: Close prices
            volume: Volume data
            
        Returns:
            OBV values
        """
        try:
            obv = pd.Series(index=close.index, dtype=float)
            obv.iloc[0] = 0
            
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
                else:
                    obv.iloc[i] = obv.iloc[i-1]
            
            return obv
            
        except Exception as e:
            raise Exception(f"Error calculating OBV: {str(e)}")
