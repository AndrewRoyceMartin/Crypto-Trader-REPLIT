# scripts/patch_app.py
import re
from pathlib import Path

APP = Path("app.py")

def insert_safe_imports(text: str) -> str:
    # Add safe shim imports once, near other top-level imports.
    if "from src.utils.safe_shims import " in text:
        return text
    pattern = r"(from flask import\s*\([\s\S]*?\)\s*\n)"
    repl = r"""\1from src.utils.safe_shims import (
    get_bollinger_target_price as safe_get_boll_target,
    get_state_store as safe_get_state_store,
    try_clear_cache,
    try_invalidate_cache,
    try_fetch_my_trades,
)
"""
    return re.sub(pattern, repl, text, count=1)

def replace_bare_except(text: str) -> str:
    # Replace 'except:' with 'except Exception as e:' and add a logger line if missing
    def _fix_block(m: re.Match) -> str:
        block = m.group(0)
        if " as e" in block:
            return block
        # try to inject logger.error if not present directly
        lines = block.splitlines()
        if len(lines) == 1:
            return "except Exception as e:"
        # add a minimal log after the except line if there isn't any log call next line
        if len(lines) >= 2 and "logger." not in lines[1]:
            lines.insert(1, "        logger.error(f\"Unhandled exception: {e}\")")
        lines[0] = "    except Exception as e:"
        return "\n".join(lines)
    return re.sub(r"\n\s*except:\s*\n(?:\s+.+\n)*", _fix_block, text)

def guard_adapter_calls(text: str) -> str:
    # Swap risky calls: .clear_cache(), .invalidate_cache(), .fetch_my_trades(), .fetch_orders()
    text = re.sub(r"(\.clear_cache\s*\(\s*\))", r"", text)
    text = re.sub(r"(\.invalidate_cache\s*\(\s*\))", r"", text)
    # Replace direct calls with guarded helper usage where clearly safe
    text = re.sub(
        r"(\bexchange\s*=\s*portfolio_service\.exchange[\s\S]{0,200}?)\n",
        r"\1\n            try_clear_cache(exchange)\n            try_invalidate_cache(exchange)\n",
        text,
        count=1,
    )
    # Replace known direct adapter calls with try_fetch_my_trades wrapper, where pattern fits
    text = re.sub(
        r"(\b[a-zA-Z_][a-zA-Z0-9_]*?)\.fetch_my_trades\s*\(",
        r"try_fetch_my_trades(\1, ",
        text,
    )
    # Fetch orders → keep but wrapped later manually by code that already guards; leave as-is if not critical.
    return text

def wire_bollinger_target(text: str) -> str:
    # Replace get_bollinger_target_price(...) with safe_get_boll_target(...)
    return text.replace("get_bollinger_target_price(", "safe_get_boll_target(")

def fix_state_store_imports(text: str) -> str:
    # Replace fragile 'from state.store import get_state_store' with safe shim alias where used in try blocks
    text = text.replace("from state.store import get_state_store", "from src.utils.safe_shims import get_state_store as get_state_store")
    # In debug helper where import is inside try: ensure fallback
    text = text.replace("get_state_store()", "safe_get_state_store()")
    return text

def remove_obvious_unused_locals(text: str) -> str:
    # Trim a few known unused variables from diagnostics if their lines exist.
    text = re.sub(r"\n\s*current_time\s*=\s*time\.time\(\)\s*\n", "\n", text)
    text = re.sub(r"\n\s*side\s*=\s*[^#\n]+\n", "\n", text)
    text = re.sub(r"\n\s*trade_value\s*=\s*[^#\n]+\n", "\n", text)
    text = re.sub(r"\n\s*end_ms\s*=\s*[^#\n]+\n", "\n", text)
    text = re.sub(r"\n\s*test_type\s*=\s*[^#\n]+\n", "\n", text)
    return text

def ensure_json_responses(text: str) -> str:
    # If a route returns a Response already, ok. If returning string where JSON expected, convert.
    # We won't overreach; rely on your existing _no_cache_json helper.
    # No-op here since your handlers already use _no_cache_json/jsonify.
    return text

def main():
    src = APP.read_text(encoding="utf-8")
    orig = src

    src = insert_safe_imports(src)
    src = wire_bollinger_target(src)
    src = fix_state_store_imports(src)
    src = replace_bare_except(src)
    src = guard_adapter_calls(src)
    src = remove_obvious_unused_locals(src)
    src = ensure_json_responses(src)

    if src != orig:
        APP.write_text(src, encoding="utf-8")
        print("✅ app.py patched")
    else:
        print("ℹ️ Nothing changed; app.py already patched")

if __name__ == "__main__":
    main()