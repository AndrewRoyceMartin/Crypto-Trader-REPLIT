# tests/test_datetime_normalization.py
from datetime import datetime, timezone
from src.utils.datetime_utils import parse_timestamp, ensure_aware, sort_by_timestamp_utc

def test_parse_timestamp_variants():
    samples = [
        "2025-09-10T03:04:56.587593Z",          # ISO Z
        "2025-09-10 03:04:56.587593",           # naive ISO-like
        datetime(2025, 9, 10, 3, 4, 56, 587593),  # naive dt
        datetime(2025, 9, 10, 3, 4, 56, 587593, tzinfo=timezone.utc),  # aware
        1694315096587,  # epoch ms
        1694315096,     # epoch s
    ]
    for s in samples:
        dt = parse_timestamp(s)
        assert dt.tzinfo is not None
        offset = dt.tzinfo.utcoffset(dt)
        assert offset is not None
        assert offset.total_seconds() == 0

def test_sort_mixed_timestamps_no_crash():
    rows = [
        {"timestamp": "2025-09-10T03:04:56Z", "id": 1},
        {"timestamp": "2025-09-09 03:04:56.587593", "id": 2},  # naive
        {"timestamp": 1694230000000, "id": 3},                 # ms
        {"timestamp": datetime(2025, 9, 11, 1, 0, 0, tzinfo=timezone.utc), "id": 4},
    ]
    sorted_rows = sort_by_timestamp_utc(rows)
    # Ensure sorted desc and tz-aware
    assert sorted_rows[0]["id"] == 4
    for r in sorted_rows:
        assert isinstance(r["timestamp"], datetime)
        assert r["timestamp"].tzinfo is not None

def test_ensure_aware_naive_to_utc():
    naive = datetime(2025, 9, 10, 0, 0, 0)
    aware = ensure_aware(naive)
    assert aware.tzinfo is not None
    offset = aware.tzinfo.utcoffset(aware)
    assert offset is not None
    assert offset.total_seconds() == 0