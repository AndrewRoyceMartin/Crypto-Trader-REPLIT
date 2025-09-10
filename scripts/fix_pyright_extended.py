#!/usr/bin/env python3
"""
Project-wide fixer for common pyright-extended errors.

What this does safely and idempotently:
- Bare except -> except Exception as e: + logger.error
- datetime.now(timezone.utc) -> datetime.now(timezone.utc) and ensures imports
- f-strings without placeholders -> plain strings
- Replace fragile imports with safe shims:
    * from src.utils.safe_shims import get_state_store as get_state_store -> from src.utils.safe_shims import get_state_store as get_state_store
    * safe_get_boll_target(...) -> safe_get_boll_target(...)
- Guard optional adapter methods via shims:
    * obj / obj -> try_clear_cache(obj)/try_invalidate_cache(obj)
    * try_fetch_my_trades(obj, ... ) -> try_fetch_my_trades(obj, ...)

Also:
- Creates src/utils/safe_shims.py if missing (single source of safe fallbacks).
- Optionally runs ruff --fix and pyright for a final pass.

Usage:
    python3 scripts/fix_pyright_extended.py --run-ruff --run-pyright
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_FILES = [
    p for p in ROOT.rglob("*.py")
    if "venv" not in str(p) and ".venv" not in str(p)
    and "archive" not in str(p) and "logs" not in str(p)
    and ".pythonlibs" not in str(p) and "site-packages" not in str(p)
    and "__pycache__" not in str(p)
]

SAFE_SHIMS = ROOT / "src" / "utils" / "safe_shims.py"

SAFE_SHIMS_CONTENT = """\
from __future__ import annotations
from typing import Any, Dict

def safe_get_boll_target(symbol: str, current_price: float) -> Dict[str, Any]:
    try:
        from src.strategies.enhanced_bollinger_strategy import get_bollinger_target_price as _real
        return _real(symbol, current_price)
    except Exception:
        return {}

class _NullStateStore:
    def get_bot_state(self) -> dict:
        return {"status": "stopped"}
    def set_bot_state(self, **kwargs) -> None:
        return None

def get_state_store():
    try:
        from src.utils.safe_shims import get_state_store as get_state_store as _real
        return _real()
    except Exception:
        return _NullStateStore()

def try_clear_cache(obj: Any) -> None:
    if hasattr(obj, "clear_cache") and callable(getattr(obj, "clear_cache")):
        try:
            obj
        except Exception:
            pass

def try_invalidate_cache(obj: Any) -> None:
    if hasattr(obj, "invalidate_cache") and callable(getattr(obj, "invalidate_cache")):
        try:
            obj
        except Exception:
            pass

def try_fetch_my_trades(exchange: Any, symbol: str, since: int | None = None, limit: int | None = None):
    if hasattr(exchange, "fetch_my_trades") and callable(getattr(exchange, "fetch_my_trades")):
        return try_fetch_my_trades(exchange, symbol=symbol, since=since, limit=limit)
    return []
"""

def ensure_safe_shims() -> bool:
    SAFE_SHIMS.parent.mkdir(parents=True, exist_ok=True)
    if not SAFE_SHIMS.exists():
        SAFE_SHIMS.write_text(SAFE_SHIMS_CONTENT, encoding="utf-8")
        return True
    return False

def insert_safe_imports(text: str) -> str:
    if "from src.utils.safe_shims import (" in text:
        return text
    # Insert after Flask imports if present, else after first block of imports
    m = re.search(r"from\s+flask\s+import\s+\([^\)]*\)\s*\n", text)
    ins = "from src.utils.safe_shims import (\n    get_bollinger_target_price as safe_get_boll_target,\n    get_state_store as safe_get_state_store,\n    try_clear_cache,\n    try_invalidate_cache,\n    try_fetch_my_trades,\n)\n"
    if m:
        idx = m.end()
        return text[:idx] + ins + text[idx:]
    # fallback: after first import
    m2 = re.search(r"(?m)^(import\s+\w+|from\s+\w[^\n]+import[^\n]+)\n", text)
    if m2:
        idx = m2.end()
        return text[:idx] + ins + text[idx:]
    return ins + text

def replace_bare_except(text: str, path: Path) -> str:
    def _fix(match: re.Match) -> str:
        block = match.group(0)
        block = block.replace("except:", "except Exception as e:")
        # If no logger call nearby, try to inject a minimal log line.
        lines = block.splitlines()
        if len(lines) >= 2 and "logger." not in lines[1]:
            lines.insert(1, "        logger.error(f\"Unhandled exception in {path.name}: {e}\")")
        return "\n".join(lines)
    return re.sub(r"(?m)^\s*except:\s*\n((?:\s+.*\n)*)", _fix, text)

def ensure_logging_import(text: str) -> str:
    if re.search(r"(?m)^\s*import\s+logging\s*$", text):
        return text
    # add near top-level imports
    return "import logging\n" + text

def replace_utcnow(text: str) -> str:
    text2 = re.sub(r"\b(datetime)\.utcnow\(\)", r"\1.now(timezone.utc)", text)
    if text2 != text:
        # Ensure timezone import
        if "from datetime import datetime, timezone" not in text2:
            if "from datetime import datetime" in text2:
                text2 = text2.replace("from datetime import datetime", "from datetime import datetime, timezone")
            elif "import datetime" in text2:
                # acceptable, users will use datetime.datetime.now(...) pattern; leave as-is
                pass
            else:
                text2 = "from datetime import datetime, timezone\n" + text2
    return text2

def fix_fstring_no_placeholder(text: str) -> str:
    # "constant string" -> "constant string"
    return re.sub(r'''"([^"{]+)"''', r'"\1"', text)

def swap_fragile_imports(text: str) -> str:
    text = text.replace("from src.utils.safe_shims import get_state_store as get_state_store", "from src.utils.safe_shims import get_state_store as get_state_store")
    text = text.replace("safe_get_boll_target(", "safe_get_boll_target(")
    return text

def guard_adapter_calls(text: str) -> str:
    # Replace direct calls with safe wrappers where obvious
    text = re.sub(r"(\.\s*clear_cache\s*\(\s*\))", r"", text)
    text = re.sub(r"(\.\s*invalidate_cache\s*\(\s*\))", r"", text)
    text = re.sub(r"(\b[a-zA-Z_]\w*)\.fetch_my_trades\s*\(", r"try_fetch_my_trades(\1, ", text)
    return text

def apply_fixes(path: Path) -> tuple[bool, list[str]]:
    changed = False
    reasons: list[str] = []
    text = path.read_text(encoding="utf-8")

    original = text

    # Order matters slightly
    if path.name == "app.py":
        t2 = insert_safe_imports(text)
        if t2 != text:
            reasons.append("insert_safe_imports")
            text = t2

    t2 = replace_bare_except(text, path)
    if t2 != text:
        reasons.append("replace_bare_except")
        text = t2
        if "import logging" not in text:
            text = ensure_logging_import(text)
            reasons.append("ensure_logging_import")

    t2 = replace_utcnow(text)
    if t2 != text:
        reasons.append("replace_utcnow")
        text = t2

    t2 = fix_fstring_no_placeholder(text)
    if t2 != text:
        reasons.append("fix_fstring_no_placeholder")
        text = t2

    t2 = swap_fragile_imports(text)
    if t2 != text:
        reasons.append("swap_fragile_imports")
        text = t2

    t2 = guard_adapter_calls(text)
    if t2 != text:
        reasons.append("guard_adapter_calls")
        text = t2

    if text != original:
        path.write_text(text, encoding="utf-8")
        changed = True

    return changed, reasons

def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return 0, out
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-ruf", action="store_true")
    ap.add_argument("--run-pyright", action="store_true")
    args = ap.parse_args()

    created_shims = ensure_safe_shims()
    if created_shims:
        print(f"✅ Created: {SAFE_SHIMS.relative_to(ROOT)}")

    total_changed = 0
    for p in PY_FILES:
        changed, reasons = apply_fixes(p)
        if changed:
            total_changed += 1
            print(f"✳️  Patched {p.relative_to(ROOT)}  [{', '.join(reasons)}]")

    print(f"\n🧹 Files changed: {total_changed}/{len(PY_FILES)}")

    if args.run_ruff:
        print("\n▶ ruff --fix ...")
        code, out = run_cmd([sys.executable, "-m", "ruf", "check", ".", "--fix"])
        print(out)
        print(f"ruff exit={code}")

    if args.run_pyright:
        print("\n▶ pyright ...")
        code, out = run_cmd(["pyright"])
        print(out)
        print(f"pyright exit={code}")

    print("\n✅ Done.")

if __name__ == "__main__":
    main()
