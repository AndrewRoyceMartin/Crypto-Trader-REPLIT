"""
Data manager for handling OHLCV data retrieval and caching.
"""

import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional
from .cache import DataCache
from ..exchanges.base import BaseExchange


class DataManager:
    """Data manager class for OHLCV data."""
    
    def __init__(self, exchange: BaseExchange, cache_enabled: bool = True):
        """
        Initialize data manager.
        
        Args:
            exchange: Exchange adapter
            cache_enabled: Whether to enable caching
        """
        self.exchange = exchange
        self.cache = DataCache() if cache_enabled else None
        self.logger = logging.getLogger(__name__)
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100, 
                  start_time: Optional[datetime] = None, 
                  end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get OHLCV data with caching support.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Number of candles
            start_time: Start time for historical data
            end_time: End time for historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{timeframe}_{limit}"
        
        # Try to get from cache first
        if self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                self.logger.debug(f"Retrieved {symbol} data from cache")
                return cached_data
        
        try:
            # Fetch fresh data from exchange
            self.logger.debug(f"Fetching {symbol} data from exchange")
            data = self.exchange.get_ohlcv(symbol, timeframe, limit)
            
            # Filter by time range if specified
            if start_time:
                data = data[data.index >= start_time]
            if end_time:
                data = data[data.index <= end_time]
            
            # Cache the data
            if self.cache:
                self.cache.set(cache_key, data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV data: {str(e)}")
            raise
    
    def get_historical_data(self, symbol: str, timeframe: str, 
                           start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get historical OHLCV data for a date range.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with historical OHLCV data
        """
        all_data = []
        current_date = start_date
        
        # Calculate days per request based on timeframe
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        max_candles = 1000  # Most exchanges limit to 1000 candles per request
        days_per_request = (max_candles * timeframe_minutes) // (24 * 60)
        
        while current_date < end_date:
            try:
                # Calculate end date for this batch
                batch_end = min(current_date + timedelta(days=days_per_request), end_date)
                
                # Fetch data for this batch
                data = self.get_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=max_candles,
                    start_time=current_date,
                    end_time=batch_end
                )
                
                if not data.empty:
                    all_data.append(data)
                
                current_date = batch_end + timedelta(minutes=timeframe_minutes)
                
            except Exception as e:
                self.logger.warning(f"Error fetching batch from {current_date}: {str(e)}")
                current_date += timedelta(days=1)  # Skip to next day
        
        # Combine all data
        if all_data:
            combined_data = pd.concat(all_data)
            combined_data = combined_data.sort_index().drop_duplicates()
            return combined_data
        else:
            return pd.DataFrame()
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """
        Convert timeframe string to minutes.
        
        Args:
            timeframe: Timeframe string (1m, 5m, 1h, 1d, etc.)
            
        Returns:
            Number of minutes
        """
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
            '1w': 10080
        }
        
        return timeframe_map.get(timeframe, 60)  # Default to 1 hour
    
    def update_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Update data with latest candles.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            Updated DataFrame
        """
        try:
            # Get latest data
            latest_data = self.exchange.get_ohlcv(symbol, timeframe, limit=1)
            
            # Update cache if enabled
            if self.cache:
                cache_key = f"{symbol}_{timeframe}"
                cached_data = self.cache.get(cache_key)
                
                if cached_data is not None:
                    # Append new data to cached data
                    updated_data = pd.concat([cached_data, latest_data])
                    updated_data = updated_data.sort_index().drop_duplicates()
                    
                    # Keep only recent data to prevent cache from growing too large
                    cutoff_time = datetime.now() - timedelta(days=30)
                    updated_data = updated_data[updated_data.index >= cutoff_time]
                    
                    self.cache.set(cache_key, updated_data)
                    return updated_data
            
            return latest_data
            
        except Exception as e:
            self.logger.error(f"Error updating data: {str(e)}")
            raise
