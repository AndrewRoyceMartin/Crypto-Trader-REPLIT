# src/utils/datetime_utils.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Any, List, Union, Optional

import re

_ISO_Z_RE = re.compile(r"Z$")

def ensure_aware(dt: datetime) -> datetime:
    """Return a UTC-aware datetime. Convert naive -> UTC, aware -> UTC."""
    if dt.tzinfo is None:
        # Treat naive as UTC (app default). If your system wants local->UTC, change here.
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def parse_timestamp(value: Union[str, int, float, datetime]) -> datetime:
    """
    Parse many timestamp formats into UTC-aware datetime:
    - datetime (naive or aware)
    - ISO 8601 strings with/without 'Z'
    - epoch seconds or ms (int/float)
    """
    if isinstance(value, datetime):
        return ensure_aware(value)

    if isinstance(value, (int, float)):
        # Heuristic: treat >1e12 as ms, otherwise seconds
        ts = float(value)
        if ts > 1e12:
            return datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(value, str):
        s = value.strip()
        # Add 'Z' if it looks like iso without tz
        if _ISO_Z_RE.search(s) is None and re.search(r"[TZ:+-]", s) is None:
            # No TZ info – treat as UTC
            try:
                dt = datetime.fromisoformat(s)
                return ensure_aware(dt)
            except ValueError:
                pass
        # Robust parse paths
        try:
            # Python 3.11+: fromisoformat handles most ISO (with offset)
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return ensure_aware(dt)
        except ValueError:
            # Last resort: try several common formats
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    return ensure_aware(datetime.strptime(s, fmt))
                except ValueError:
                    continue

    # Fallback: now (UTC) to avoid crashes, but better to raise in dev:
    return datetime.now(timezone.utc)

def normalize_records_timestamp_key(
    rows: Iterable[Mapping[str, Any]],
    key: str = "timestamp",
    out_key: Optional[str] = None,
) -> List[dict]:
    """
    Return new list with rows' `key` coerced to UTC-aware datetime (stored back or into out_key).
    """
    out: List[dict] = []
    target_key = out_key or key
    for r in rows:
        d = dict(r)
        value = d.get(key)
        if value is not None:
            d[target_key] = parse_timestamp(value)
        else:
            d[target_key] = datetime.now(timezone.utc)  # fallback for None values
        out.append(d)
    return out

def sort_by_timestamp_utc(rows: Iterable[Mapping[str, Any]], key: str = "timestamp", reverse: bool = True) -> List[dict]:
    """Sort rows by UTC-aware timestamp descending by default."""
    nr = normalize_records_timestamp_key(rows, key=key)
    return sorted(nr, key=lambda r: r[key], reverse=reverse)