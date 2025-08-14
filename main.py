#!/usr/bin/env python3
"""
Main entry point for the algorithmic trading system.
Supports multiple modes: backtest, paper trading, live trading, and web interface.
"""

import sys
import os

def run_backtest() -> None:
    """Run backtesting mode using bot.py implementation."""
    from bot import run_backtest as bot_backtest
    bot_backtest()

def run_paper() -> None:
    """Run paper trading mode using bot.py implementation."""
    from bot import run_paper as bot_paper
    bot_paper()

def run_live() -> None:
    """Run live trading mode using bot.py implementation."""
    from bot import run_paper as bot_paper  # Note: using paper for now as live needs more setup
    bot_paper()

def run_web() -> None:
    """Run web interface mode."""
    from web_interface import app, initialize_system
    initialize_system()
    port = int(os.environ.get("PORT", "5000"))  # Use PORT env var for Replit deployment
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "web":
            run_web()
        elif mode == "paper":
            run_paper()
        elif mode == "live":
            run_live()
        elif mode == "backtest":
            run_backtest()
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: web, paper, live, backtest")
            sys.exit(1)
    else:
        print("Usage: python main.py <mode>")
        print("Available modes: web, paper, live, backtest")
        sys.exit(1)
