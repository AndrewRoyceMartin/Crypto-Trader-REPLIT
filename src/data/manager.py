"""
Data manager for handling OHLCV data retrieval and caching.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Hashable, cast, Dict, List

import pandas as pd

from .cache import DataCache
from ..exchanges.base import BaseExchange


class DataManager:
    """Data manager class for OHLCV data with safe typing and caching."""

    def __init__(self, exchange: BaseExchange, cache_enabled: bool = True) -> None:
        """
        Initialize data manager.

        Args:
            exchange: Exchange adapter
            cache_enabled: Whether to enable caching
        """
        self.exchange: BaseExchange = exchange
        self.cache: Optional[DataCache] = DataCache() if cache_enabled else None
        self.logger = logging.getLogger(__name__)

    # ---------------------------
    # Public API
    # ---------------------------
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Get OHLCV data with optional time filtering and cache.

        Returns:
            DataFrame indexed by UTC DatetimeIndex with columns:
            ["open","high","low","close","volume"]
        """
        cache_key = self._cache_key(symbol, timeframe, limit, start_time, end_time)

        # Try cache
        if self.cache is not None:
            cached_any: Any = self.cache.get(cache_key)
            cached_df = cast(pd.DataFrame, self._coerce_df(cached_any))
            if not cached_df.empty:
                cached_df = self._ensure_dt_index(cached_df)
                return cached_df

        # Fetch fresh
        try:
            raw: Any = self.exchange.get_ohlcv(symbol, timeframe, limit)
            df = cast(pd.DataFrame, self._ensure_dt_index(self._coerce_df(raw)))

            # Time filters
            if start_time is not None:
                st = self._to_utc_ts(start_time)
                df = df[df.index >= st]
            if end_time is not None:
                et = self._to_utc_ts(end_time)
                df = df[df.index <= et]

            # Cache
            if self.cache is not None:
                self.cache.set(cache_key, cast(pd.DataFrame, df))

            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {symbol} {timeframe}: {e}")
            return self._empty_df()

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data for a date range.

        Returns:
            DataFrame with OHLCV data indexed by UTC DatetimeIndex.
        """
        start_utc = self._to_utc_ts(start_date)
        end_utc = self._to_utc_ts(end_date)
        if start_utc >= end_utc:
            return self._empty_df()

        all_chunks: List[pd.DataFrame] = []
        max_candles = 1000
        minutes_per_bar = max(1, self._timeframe_to_minutes(timeframe))
        days_per_request = max(1, (max_candles * minutes_per_bar) // (24 * 60))

        cur = start_utc
        while cur < end_utc:
            batch_end = min(cur + timedelta(days=days_per_request), end_utc)
            chunk = self.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=max_candles,
                start_time=cur,
                end_time=batch_end,
            )
            if not chunk.empty:
                all_chunks.append(chunk)
            cur = batch_end + timedelta(minutes=minutes_per_bar)

        if not all_chunks:
            return self._empty_df()

        combined = cast(pd.DataFrame, pd.concat(all_chunks, axis=0))
        combined = self._ensure_dt_index(self._coerce_df(combined))
        if combined.empty:
            return combined

        combined = combined[~combined.index.duplicated(keep="last")]
        return combined.sort_index()

    def update_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Update cached data with the latest candle (if available).

        Returns:
            Updated DataFrame (or the single latest candle if no cache exists).
        """
        try:
            latest_raw: Any = self.exchange.get_ohlcv(symbol, timeframe, limit=1)
            latest = cast(pd.DataFrame, self._ensure_dt_index(self._coerce_df(latest_raw)))

            cache_key = self._cache_key(symbol, timeframe, limit=None, start=None, end=None)
            cached_any: Any = self.cache.get(cache_key) if self.cache is not None else None
            cached = cast(pd.DataFrame, self._coerce_df(cached_any))

            if not cached.empty:
                updated = cast(pd.DataFrame, pd.concat([cached, latest], axis=0))
                updated = updated[~updated.index.duplicated(keep="last")].sort_index()

                cutoff = datetime.now(timezone.utc) - timedelta(days=30)
                updated = updated[updated.index >= cutoff]

                if self.cache is not None:
                    self.cache.set(cache_key, cast(pd.DataFrame, updated))
                return updated

            if self.cache is not None:
                self.cache.set(cache_key, cast(pd.DataFrame, latest))
            return latest
        except Exception as e:
            self.logger.error(f"Error updating data for {symbol} {timeframe}: {e}")
            return self._empty_df()

    # ---------------------------
    # Helpers (typed & robust)
    # ---------------------------
    def _coerce_df(self, obj: Any) -> pd.DataFrame:
        """Coerce arbitrary input to a DataFrame; return standardized empty on failure."""
        if isinstance(obj, pd.DataFrame):
            return obj
        try:
            df_any: Any = pd.DataFrame(obj)
            df = cast(pd.DataFrame, df_any)
            if not isinstance(df, pd.DataFrame):
                return self._empty_df()
            return df
        except Exception:
            return self._empty_df()

    def _ensure_dt_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure DataFrame has a UTC DatetimeIndex, sorted ascending,
        and normalized OHLCV columns.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            return self._empty_df()

        out = df.copy()

        # Already a DatetimeIndex
        if isinstance(out.index, pd.DatetimeIndex):
            idx = cast(pd.DatetimeIndex, out.index)
            if idx.tz is None:
                idx = idx.tz_localize("UTC")
            else:
                idx = idx.tz_convert("UTC")
            out.index = idx
            out = out.sort_index()
            return self._normalize_ohlcv_columns(out)

        # Try to build index from a timestamp-like column
        ts_col: Optional[str] = None
        for cand in ("ts", "timestamp", "date", "time"):
            if cand in out.columns:
                ts_col = cand
                break

        if ts_col is not None:
            s = out[ts_col]
            try:
                idx_any: Any = pd.to_datetime(s, unit="ms", utc=True, errors="coerce")
                idx = cast(pd.DatetimeIndex, idx_any)
                if idx.isna().all():
                    idx_any2: Any = pd.to_datetime(s, utc=True, errors="coerce")
                    idx = cast(pd.DatetimeIndex, idx_any2)
            except Exception:
                idx_any3: Any = pd.to_datetime(s, utc=True, errors="coerce")
                idx = cast(pd.DatetimeIndex, idx_any3)

            out.index = idx
            out = out.drop(columns=[ts_col], errors="ignore")
            out = out[~out.index.isna()]

            idx2 = cast(pd.DatetimeIndex, out.index)
            if idx2.tz is None:
                idx2 = idx2.tz_localize("UTC")
            else:
                idx2 = idx2.tz_convert("UTC")
            out.index = idx2

            out = out.sort_index()
            return self._normalize_ohlcv_columns(out)

        return self._empty_df()

    def _normalize_ohlcv_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure the frame has the standard OHLCV columns; if not, map sensible defaults.
        """
        if df.empty:
            return self._empty_df()

        cols_list: List[str] = [str(c) for c in list(df.columns)]
        cols_lower: List[str] = [c.lower() for c in cols_list]
        mapping: Dict[Hashable, str] = {}

        def _map_to(target: str, candidates: List[str]) -> None:
            for cand in candidates:
                if cand in cols_lower:
                    i = cols_lower.index(cand)
                    orig: Hashable = cast(Hashable, df.columns[i])
                    mapping[orig] = target
                    return

        _map_to("open", ["open", "o"])
        _map_to("high", ["high", "h"])
        _map_to("low", ["low", "l"])
        _map_to("close", ["close", "c"])
        _map_to("volume", ["volume", "vol", "qty", "v"])

        out = df.rename(columns=mapping, errors="ignore").copy()

        for req in ("open", "high", "low", "close", "volume"):
            if req not in out.columns:
                out[req] = 0.0

        wanted = ["open", "high", "low", "close", "volume"]
        out = cast(pd.DataFrame, out[wanted])
        return out

    def _empty_df(self) -> pd.DataFrame:
        """Standardized empty OHLCV frame with UTC DatetimeIndex."""
        empty = pd.DataFrame(columns=pd.Index(["open", "high", "low", "close", "volume"]))
        empty.index = pd.DatetimeIndex([], tz="UTC")
        return empty

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        mapping = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "6h": 360, "12h": 720,
            "1d": 1440, "1w": 10080,
        }
        return mapping.get(timeframe, 60)

    def _to_utc_ts(self, dt: datetime) -> datetime:
        """Ensure a timezone-aware UTC datetime."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _cache_key(
        self,
        symbol: str,
        timeframe: str,
        limit: Optional[int],
        start: Optional[datetime],
        end: Optional[datetime],
    ) -> str:
        """Build a stable cache key for a price request."""
        lim = str(limit) if limit is not None else "all"
        st = self._to_utc_ts(start).isoformat() if start else "none"
        et = self._to_utc_ts(end).isoformat() if end else "none"
        return f"ohlcv::{symbol}::{timeframe}::limit={lim}::start={st}::end={et}"
