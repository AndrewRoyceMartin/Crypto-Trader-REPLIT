# tests/test_app_tidy.py
import importlib
import re
from pathlib import Path

def test_app_imports_ok():
    # Ensure app imports after patch (no undefined names/import errors)
    mod = importlib.import_module("app")
    assert hasattr(mod, "app"), "Flask app should be defined"

def test_no_bare_except():
    txt = Path("app.py").read_text(encoding="utf-8")
    # crude check that no raw 'except:' remains
    assert re.search(r"\n\s*except:\s*\n", txt) is None

def test_bollinger_shim_present():
    from src.utils.safe_shims import get_bollinger_target_price
    out = get_bollinger_target_price("BTC", 100.0)
    assert isinstance(out, dict)  # shim returns dict even if strategy not installed

def test_state_store_shim_present():
    from src.utils.safe_shims import get_state_store
    store = get_state_store()
    assert hasattr(store, "get_bot_state")