"""
Web interface for the algorithmic trading system.
Provides a dashboard for monitoring and controlling trading operations.
"""

from flask import Flask, render_template, jsonify, request
import json
import logging
from datetime import datetime, timedelta
import threading
import os

from src.config import Config
from src.utils.logging import setup_logging
from src.utils.database import DatabaseManager
from src.backtesting.engine import BacktestEngine
from src.trading.paper_trader import PaperTrader
from src.trading.live_trader import LiveTrader
from src.strategies.bollinger_strategy import BollingerBandsStrategy
from src.exchanges.okx_adapter import OKXAdapter  # (kept for future use)
from src.exchanges.kraken_adapter import KrakenAdapter  # (kept for future use)

# -----------------------------------------------------------------------------
# Flask app
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "trading-system-secret-key-2024")

# -----------------------------------------------------------------------------
# Global state
# -----------------------------------------------------------------------------
config: Config | None = None
db_manager: DatabaseManager | None = None
current_trader = None
trading_thread: threading.Thread | None = None

state_lock = threading.RLock()
_initialized = False

trading_status = {
    "mode": "stopped",
    "symbol": None,
    "start_time": None,
    "is_running": False,
}

# -----------------------------------------------------------------------------
# Init / helpers
# -----------------------------------------------------------------------------
def initialize_system():
    """Initialize the trading system components (idempotent)."""
    global config, db_manager, _initialized
    if _initialized:
        return
    config = Config()
    setup_logging(config.get("logging", "level", "INFO"))
    db_manager = DatabaseManager()
    _initialized = True
    app.logger.info("Trading system initialized")

def _require_json():
    data = request.get_json(silent=True)
    if data is None:
        raise ValueError("Expected JSON body")
    return data

def start_trader_thread(mode: str, symbol: str, timeframe: str):
    """Start trader in a separate background thread."""
    global current_trader, trading_thread
    initialize_system()
    strategy = BollingerBandsStrategy(config)

    with state_lock:
        if mode == "paper":
            current_trader = PaperTrader(config, strategy)
        elif mode == "live":
            current_trader = LiveTrader(config, strategy)
        else:
            raise ValueError(f"Invalid trading mode: {mode}")

        trading_status.update(
            {
                "mode": mode,
                "symbol": symbol,
                "start_time": datetime.now(),
                "is_running": True,
            }
        )

    def _run():
        try:
            current_trader.start_trading(symbol, timeframe)
        except Exception as e:
            app.logger.exception("Trader thread crashed: %s", e)
            with state_lock:
                trading_status.update(
                    {"mode": "stopped", "symbol": None, "start_time": None, "is_running": False}
                )

    trading_thread = threading.Thread(target=_run, daemon=True)
    trading_thread.start()
    app.logger.info("Started %s trading for %s (%s)", mode, symbol, timeframe)

# Ensure initialization even if app is imported (e.g. main.py -> from web_interface import app)
initialize_system()

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/ready")
def ready():
    ok = (config is not None) and (db_manager is not None)
    code = 200 if ok else 503
    return jsonify({"ready": ok}), code

@app.route("/api/status")
def get_status():
    try:
        initialize_system()
        with state_lock:
            mode = trading_status["mode"]
        portfolio_data = get_portfolio_data()
        recent_trades = db_manager.get_trades(mode=mode, start_date=datetime.now() - timedelta(days=1))
        trades_data = recent_trades.tail(10).to_dict("records") if not recent_trades.empty else []
        positions_df = db_manager.get_positions(mode=mode)
        positions_data = positions_df.to_dict("records") if not positions_df.empty else []
        with state_lock:
            status_copy = dict(trading_status)
        return jsonify(
            {
                "trading_status": status_copy,
                "portfolio": portfolio_data,
                "recent_trades": trades_data,
                "positions": positions_data,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        app.logger.error("Error getting status: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/portfolio")
def get_portfolio():
    try:
        return jsonify(get_portfolio_data())
    except Exception as e:
        app.logger.error("Error getting portfolio: %s", e)
        return jsonify({"error": str(e)}), 500

def get_portfolio_data():
    """Assemble portfolio snapshot and last-7-days equity series."""
    initialize_system()
    try:
        if current_trader and hasattr(current_trader, "get_portfolio_value"):
            if trading_status["mode"] == "paper":
                portfolio_value = current_trader.get_portfolio_value()
                cash = getattr(current_trader, "cash", portfolio_value)
                positions_value = portfolio_value - cash
                performance = current_trader.get_performance_summary()
            else:
                # TODO: pull from live exchange adapter
                portfolio_value = 10000.0
                cash = 5000.0
                positions_value = 5000.0
                performance = {}
        else:
            initial_capital = config.get_float("backtesting", "initial_capital", 10000.0)
            portfolio_value = initial_capital
            cash = initial_capital
            positions_value = 0.0
            performance = {}

        portfolio_history = db_manager.get_portfolio_history(mode=trading_status["mode"], days=7)
        chart_data = (
            [{"timestamp": row["timestamp"].isoformat(), "value": row["total_value"]} for _, row in portfolio_history.iterrows()]
            if not portfolio_history.empty
            else []
        )

        return {
            "total_value": portfolio_value,
            "cash": cash,
            "positions_value": positions_value,
            "daily_pnl": performance.get("total_return", 0) * portfolio_value if performance else 0,
            "total_return": performance.get("total_return", 0) if performance else 0,
            "chart_data": chart_data,
        }
    except Exception as e:
        app.logger.error("Error getting portfolio data: %s", e)
        return {"total_value": 0, "cash": 0, "positions_value": 0, "daily_pnl": 0, "total_return": 0, "chart_data": []}

@app.route("/api/start_trading", methods=["POST"])
def start_trading():
    try:
        data = _require_json()
        mode = data.get("mode", "paper").lower()
        symbol = data.get("symbol", "BTC/USDT")
        timeframe = data.get("timeframe", "1h")
        if trading_status["is_running"]:
            return jsonify({"error": "Trading is already running"}), 400
        if mode == "live" and not data.get("confirmation", False):
            return jsonify({"error": "Live trading requires explicit confirmation"}), 400
        start_trader_thread(mode, symbol, timeframe)
        return jsonify({"success": True, "message": f"{mode.title()} trading started for {symbol}"})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error("Error starting trading: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/stop_trading", methods=["POST"])
def stop_trading():
    try:
        global current_trader
        if not trading_status["is_running"]:
            return jsonify({"error": "Trading is not running"}), 400
        if current_trader:
            current_trader.stop_trading()
        with state_lock:
            trading_status.update({"mode": "stopped", "symbol": None, "start_time": None, "is_running": False})
        return jsonify({"success": True, "message": "Trading stopped"})
    except Exception as e:
        app.logger.error("Error stopping trading: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/backtest", methods=["POST"])
def run_backtest():
    try:
        data = _require_json()
        symbol = data.get("symbol", "BTC/USDT")
        days = int(data.get("days", 30))
        timeframe = data.get("timeframe", "1h")

        strategy = BollingerBandsStrategy(config)
        engine = BacktestEngine(config, strategy)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        results = engine.run_backtest(symbol=symbol, start_date=start_date, end_date=end_date, timeframe=timeframe)

        performance_data = {
            "strategy_name": "BollingerBands",
            "symbol": symbol,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "total_return": results.get("total_return", 0),
            "sharpe_ratio": results.get("sharpe_ratio", 0),
            "max_drawdown": results.get("max_drawdown", 0),
            "total_trades": results.get("total_trades", 0),
            "win_rate": results.get("win_rate", 0),
            "mode": "backtest",
        }
        db_manager.save_strategy_performance(performance_data)
        return jsonify({"success": True, "results": results})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error("Error running backtest: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/trades")
def get_trades():
    try:
        mode = request.args.get("mode", trading_status["mode"])
        symbol = request.args.get("symbol")
        days = int(request.args.get("days", 7))
        start_date = datetime.now() - timedelta(days=days)
        trades_df = db_manager.get_trades(symbol=symbol, start_date=start_date, mode=mode)
        return jsonify(trades_df.to_dict("records") if not trades_df.empty else [])
    except Exception as e:
        app.logger.error("Error getting trades: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/positions")
def get_positions():
    try:
        mode = request.args.get("mode", trading_status["mode"])
        positions_df = db_manager.get_positions(mode=mode)
        return jsonify(positions_df.to_dict("records") if not positions_df.empty else [])
    except Exception as e:
        app.logger.error("Error getting positions: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/config")
def get_config():
    try:
        return jsonify(
            {
                "trading": {
                    "default_symbol": config.get("trading", "default_symbol", "BTC/USDT"),
                    "default_timeframe": config.get("trading", "default_timeframe", "1h"),
                    "position_size_percent": config.get_float("trading", "position_size_percent", 5.0),
                    "max_positions": config.get_int("trading", "max_positions", 3),
                },
                "risk": {
                    "max_portfolio_risk": config.get_float("risk", "max_portfolio_risk", 10.0),
                    "max_single_position_risk": config.get_float("risk", "max_single_position_risk", 5.0),
                    "max_daily_loss": config.get_float("risk", "max_daily_loss", 5.0),
                },
                "strategy": {
                    "bb_period": config.get_int("strategy", "bb_period", 20),
                    "bb_std_dev": config.get_float("strategy", "bb_std_dev", 2.0),
                    "atr_period": config.get_int("strategy", "atr_period", 14),
                },
            }
        )
    except Exception as e:
        app.logger.error("Error getting config: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/emergency_stop", methods=["POST"])
def emergency_stop():
    try:
        global current_trader
        if current_trader and hasattr(current_trader, "emergency_stop"):
            current_trader.emergency_stop()
        elif current_trader:
            current_trader.stop_trading()
        with state_lock:
            trading_status.update({"mode": "stopped", "symbol": None, "start_time": None, "is_running": False})
        app.logger.critical("EMERGENCY STOP ACTIVATED")
        return jsonify({"success": True, "message": "Emergency stop activated"})
    except Exception as e:
        app.logger.error("Error in emergency stop: %s", e)
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Internal error: %s", error)
    return jsonify({"error": "Internal server error"}), 500

# -----------------------------------------------------------------------------
# Entrypoint (Replit binds to $PORT)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    initialize_system()
    port = int(os.environ.get("PORT", "5000"))  # Replit injects PORT at runtime
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
