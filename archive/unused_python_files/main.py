#!/usr/bin/env python3
"""
Main entry point for the algorithmic trading system.

Modes:
  - web       : Flask web UI
  - backtest  : Historical backtesting and optimization
  - live      : Live trading with real OKX account
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from typing import Literal

Mode = Literal["web", "live", "backtest"]


def run_backtest() -> None:
    """Run backtesting mode using bot.py implementation."""
    # Local import to keep startup fast and avoid import cycles
    from bot import run_backtest as bot_backtest
    bot_backtest()


def run_live() -> None:
    """Run live trading backtesting and optimization."""
    import sys

    from bot import run_backtest, run_optimize

    arg = sys.argv[2].lower() if len(sys.argv) > 2 else ""
    if arg == "opt":
        run_optimize()
    else:
        run_backtest()


def run_web() -> None:
    """Run web interface mode."""
    # Try both common module names to avoid import/name churn
    try:
        from app import app, initialize_system
    except Exception:
        from web_interface import app, initialize_system  # type: ignore[no-redef]

    initialize_system()
    port_str = os.environ.get("PORT", "5000")
    try:
        port = int(port_str)
    except ValueError:
        port = 5000
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def parse_args(argv: Sequence[str] | None = None) -> Mode:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Run trading system in different modes.",
    )
    parser.add_argument(
        "mode",
        choices=["web", "live", "backtest"],
        help="Mode to run",
    )
    ns = parser.parse_args(argv)
    return ns.mode  # type: ignore[return-value]


def main(argv: Sequence[str] | None = None) -> int:
    mode = parse_args(argv)

    if mode == "web":
        run_web()
    elif mode == "live":
        run_live()
    else:  # backtest
        run_backtest()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
