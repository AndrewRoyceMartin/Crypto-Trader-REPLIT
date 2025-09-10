"""
Data caching system for OHLCV data.
"""

import logging
import os
import pickle
import sqlite3
from datetime import datetime, timedelta

import pandas as pd


class DataCache:
    """Data caching system using SQLite and pickle."""

    def __init__(self, cache_duration_hours: int = 1, db_path: str = "cache.db"):
        """
        Initialize data cache.

        Args:
            cache_duration_hours: How long to cache data in hours
            db_path: Path to SQLite database file
        """
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for caching."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    data BLOB,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error initializing cache database: {e!s}")

    def get(self, key: str) -> pd.DataFrame | None:
        """
        Get data from cache.

        Args:
            key: Cache key

        Returns:
            Cached DataFrame or None if not found/expired
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT data, expires_at FROM cache WHERE key = ?',
                (key,)
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                data_blob, expires_at = result
                expires_at = datetime.fromisoformat(expires_at)

                # Check if data has expired
                if datetime.now() < expires_at:
                    data = pickle.loads(data_blob)
                    self.logger.debug(f"Cache hit for key: {key}")
                    return data
                else:
                    # Remove expired data
                    self.delete(key)
                    self.logger.debug(f"Cache expired for key: {key}")

            return None

        except Exception as e:
            self.logger.error(f"Error retrieving from cache: {e!s}")
            return None

    def set(self, key: str, data: pd.DataFrame):
        """
        Store data in cache.

        Args:
            key: Cache key
            data: DataFrame to cache
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            created_at = datetime.now()
            expires_at = created_at + self.cache_duration
            data_blob = pickle.dumps(data)

            cursor.execute('''
                INSERT OR REPLACE INTO cache (key, data, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (key, data_blob, created_at.isoformat(), expires_at.isoformat()))

            conn.commit()
            conn.close()

            self.logger.debug(f"Data cached for key: {key}")

        except Exception as e:
            self.logger.error(f"Error storing in cache: {e!s}")

    def delete(self, key: str):
        """
        Delete data from cache.

        Args:
            key: Cache key to delete
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))

            conn.commit()
            conn.close()

            self.logger.debug(f"Cache entry deleted: {key}")

        except Exception as e:
            self.logger.error(f"Error deleting from cache: {e!s}")

    def clear_expired(self):
        """Clear all expired cache entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'DELETE FROM cache WHERE expires_at < ?',
                (datetime.now().isoformat(),)
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted_count > 0:
                self.logger.info(f"Cleared {deleted_count} expired cache entries")

        except Exception as e:
            self.logger.error(f"Error clearing expired cache: {e!s}")

    def clear_all(self):
        """Clear all cache entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM cache')

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            self.logger.info(f"Cleared all cache entries ({deleted_count} entries)")

        except Exception as e:
            self.logger.error(f"Error clearing all cache: {e!s}")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM cache')
            total_entries = cursor.fetchone()[0]

            cursor.execute(
                'SELECT COUNT(*) FROM cache WHERE expires_at > ?',
                (datetime.now().isoformat(),)
            )
            valid_entries = cursor.fetchone()[0]

            # Get database file size
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

            conn.close()

            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'expired_entries': total_entries - valid_entries,
                'file_size_mb': file_size / (1024 * 1024)
            }

        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e!s}")
            return {}
