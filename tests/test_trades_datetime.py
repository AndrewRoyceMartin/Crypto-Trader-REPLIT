# tests/test_trades_datetime.py
from datetime import datetime, timezone
from app import app

def test_trades_endpoint_sorts_and_serializes(monkeypatch):
    def fake_load_signals():
        return [
            {"timestamp": "2025-09-10T03:04:56.587593Z", "signal_type": "SIGNAL", "id": "s1"},
            {"timestamp": "2025-09-09 03:04:56.500000",   "signal_type": "SIGNAL", "id": "s2"},
        ]
    def fake_load_exec():
        return [
            {"timestamp": 1694230000000, "signal_type": "EXECUTED_TRADE", "id": "e1"}, # ms
            {"timestamp": datetime(2025, 9, 11, 1, 0, 0, tzinfo=timezone.utc), "signal_type": "EXECUTED_TRADE", "id": "e2"},
        ]

    import app as app_mod
    monkeypatch.setattr(app_mod, "load_signals", fake_load_signals)
    monkeypatch.setattr(app_mod, "load_executed_trades", fake_load_exec)

    with app.test_client() as c:
        r = c.get("/api/trades")
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        rows = data["trades"]
        assert all(isinstance(x["timestamp"], str) and x["timestamp"].endswith("Z") for x in rows)
        # ensure sorted desc
        assert rows[0]["id"] == "e2"