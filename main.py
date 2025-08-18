#!/usr/bin/env python3
"""
Main entry point for the algorithmic trading system.

Modes:
  - web       : Flask web UI
  - paper     : Paper trading (OKX demo)
  - live      : Alias to paper for now
  - backtest  : Backtest using bot.py
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Literal, Sequence


Mode = Literal["web", "paper", "live", "backtest"]


def run_backtest() -> None:
    """Run backtesting mode using bot.py implementation."""
    # Local import to keep startup fast and avoid import cycles
    from bot import run_backtest as bot_backtest  # noqa: WPS433 (local import on purpose)
    bot_backtest()


def run_paper() -> None:
    """Run paper trading mode using bot.py implementation."""
    from bot import run_paper as bot_paper  # noqa: WPS433
    bot_paper()


def run_live() -> None:
    """Run live trading mode (currently aliases paper)."""
    from bot import run_paper as bot_paper  # noqa: WPS433
    bot_paper()


def run_web() -> None:
    """Run web interface mode."""
    # Try both common module names to avoid import/name churn
    try:
        from app import app, initialize_system  # noqa: WPS433
    except Exception:
        from web_interface import app, initialize_system  # type: ignore[no-redef]  # noqa: WPS433

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
        choices=["web", "paper", "live", "backtest"],
        help="Mode to run",
    )
    ns = parser.parse_args(argv)
    return ns.mode  # type: ignore[return-value]


def main(argv: Sequence[str] | None = None) -> int:
    mode = parse_args(argv)

    if mode == "web":
        run_web()
    elif mode == "paper":
        run_paper()
    elif mode == "live":
        run_live()
    else:  # backtest
        run_backtest()

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
