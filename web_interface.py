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
from src.data.crypto_portfolio import CryptoPortfolioManager

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
crypto_portfolio: CryptoPortfolioManager | None = None
portfolio_update_thread: threading.Thread | None = None
backtest_results: dict = {}

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
    global config, db_manager, crypto_portfolio, _initialized
    if _initialized:
        return
    config = Config()
    setup_logging(config.get("logging", "level", "INFO"))
    db_manager = DatabaseManager()
    
    # Initialize crypto portfolio with 100 cryptos at $100 each
    crypto_portfolio = CryptoPortfolioManager(initial_value_per_crypto=100.0)
    crypto_portfolio.load_portfolio_state()  # Load existing state if available
    
    # Start background price simulation
    start_portfolio_updates()
    
    _initialized = True
    app.logger.info("Trading system initialized with crypto portfolio")

def start_portfolio_updates():
    """Start background thread to update crypto portfolio prices."""
    global portfolio_update_thread
    
    def update_prices():
        import time
        while True:
            try:
                if crypto_portfolio:
                    crypto_portfolio.simulate_price_movements()
                    crypto_portfolio.save_portfolio_state()
                time.sleep(60)  # Update every minute
            except Exception as e:
                app.logger.error(f"Error updating portfolio prices: {e}")
                time.sleep(60)
    
    if portfolio_update_thread is None or not portfolio_update_thread.is_alive():
        portfolio_update_thread = threading.Thread(target=update_prices, daemon=True)
        portfolio_update_thread.start()
        app.logger.info("Started crypto portfolio price updates")

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
                "backtest_results": backtest_results,
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

@app.route("/api/portfolio/history")
def get_portfolio_history():
    """Get extended portfolio history for charting."""
    try:
        initialize_system()
        days = request.args.get('days', 30, type=int)
        mode = request.args.get('mode', trading_status["mode"])
        
        portfolio_history = db_manager.get_portfolio_history(mode=mode, days=days)
        
        if not portfolio_history.empty:
            history_data = [
                {
                    "timestamp": row["timestamp"].isoformat(),
                    "value": row["total_value"],
                    "cash": row.get("cash", 0),
                    "positions_value": row.get("positions_value", 0)
                } 
                for _, row in portfolio_history.iterrows()
            ]
        else:
            # Return current snapshot if no history
            portfolio_data = get_portfolio_data()
            current_time = datetime.now()
            history_data = [{
                "timestamp": current_time.isoformat(),
                "value": portfolio_data["total_value"],
                "cash": portfolio_data["cash"],
                "positions_value": portfolio_data["positions_value"]
            }]
        
        return jsonify({
            "history": history_data,
            "period_days": days,
            "mode": mode
        })
        
    except Exception as e:
        app.logger.error("Error getting portfolio history: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/crypto-portfolio")
def get_crypto_portfolio():
    """Get detailed cryptocurrency portfolio data."""
    try:
        initialize_system()
        if not crypto_portfolio:
            return jsonify({"error": "Crypto portfolio not initialized"}), 500
        
        summary = crypto_portfolio.get_portfolio_summary()
        portfolio_data = crypto_portfolio.get_portfolio_data()
        
        # Convert to list format for easier frontend consumption
        crypto_list = []
        for symbol, data in portfolio_data.items():
            crypto_list.append({
                "symbol": symbol,
                "name": data["name"],
                "rank": data["rank"],
                "quantity": round(data["quantity"], 6),
                "current_price": round(data["current_price"], 4),
                "current_value": round(data["current_value"], 2),
                "initial_value": data["initial_value"],
                "pnl": round(data["pnl"], 2),
                "pnl_percent": round(data["pnl_percent"], 2)
            })
        
        # Sort by current value (largest positions first)
        crypto_list.sort(key=lambda x: x["current_value"], reverse=True)
        
        return jsonify({
            "summary": {
                "total_cryptos": summary["number_of_cryptos"],
                "total_initial_value": round(summary["total_initial_value"], 2),
                "total_current_value": round(summary["total_current_value"], 2),
                "total_pnl": round(summary["total_pnl"], 2),
                "total_pnl_percent": round(summary["total_pnl_percent"], 2),
                "top_gainers": summary["top_gainers"],
                "top_losers": summary["top_losers"],
                "largest_positions": summary["largest_positions"]
            },
            "cryptocurrencies": crypto_list
        })
        
    except Exception as e:
        app.logger.error("Error getting crypto portfolio: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/rebalance-portfolio", methods=["POST"])
def rebalance_crypto_portfolio():
    """Rebalance the cryptocurrency portfolio to equal weights."""
    try:
        initialize_system()
        if not crypto_portfolio:
            return jsonify({"error": "Crypto portfolio not initialized"}), 500
        
        # Reset all positions to $100 each but keep price history
        portfolio_data = crypto_portfolio.get_portfolio_data()
        for symbol, data in portfolio_data.items():
            current_price = data["current_price"]
            new_quantity = 100.0 / current_price
            
            crypto_portfolio.portfolio_data[symbol]["quantity"] = new_quantity
            crypto_portfolio.portfolio_data[symbol]["initial_value"] = 100.0
            crypto_portfolio.portfolio_data[symbol]["current_value"] = new_quantity * current_price
            crypto_portfolio.portfolio_data[symbol]["pnl"] = crypto_portfolio.portfolio_data[symbol]["current_value"] - 100.0
            crypto_portfolio.portfolio_data[symbol]["pnl_percent"] = (crypto_portfolio.portfolio_data[symbol]["pnl"] / 100.0) * 100
        
        crypto_portfolio.save_portfolio_state()
        return jsonify({"success": True, "message": "Portfolio rebalanced successfully"})
        
    except Exception as e:
        app.logger.error("Error rebalancing portfolio: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reset-portfolio", methods=["POST"])
def reset_crypto_portfolio():
    """Reset the cryptocurrency portfolio to initial state."""
    global crypto_portfolio
    try:
        initialize_system()
        if not crypto_portfolio:
            return jsonify({"error": "Crypto portfolio not initialized"}), 500
        
        # Reinitialize the entire portfolio
        crypto_portfolio = CryptoPortfolioManager(initial_value_per_crypto=100.0)
        crypto_portfolio.save_portfolio_state()
        
        return jsonify({"success": True, "message": "Portfolio reset successfully"})
        
    except Exception as e:
        app.logger.error("Error resetting portfolio: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/export-portfolio")
def export_crypto_portfolio():
    """Export cryptocurrency portfolio data as CSV."""
    try:
        initialize_system()
        if not crypto_portfolio:
            return jsonify({"error": "Crypto portfolio not initialized"}), 500
        
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Rank', 'Symbol', 'Name', 'Quantity', 'Current Price', 'Current Value', 'Initial Value', 'PnL', 'PnL %'])
        
        # Write data
        portfolio_data = crypto_portfolio.get_portfolio_data()
        for symbol, data in sorted(portfolio_data.items(), key=lambda x: x[1]['rank']):
            writer.writerow([
                data['rank'],
                symbol,
                data['name'],
                round(data['quantity'], 6),
                round(data['current_price'], 6),
                round(data['current_value'], 2),
                data['initial_value'],
                round(data['pnl'], 2),
                round(data['pnl_percent'], 2)
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=crypto_portfolio.csv'}
        )
        
    except Exception as e:
        app.logger.error("Error exporting portfolio: %s", e)
        return jsonify({"error": str(e)}), 500

def get_portfolio_data():
    """Assemble portfolio snapshot and last-7-days equity series."""
    initialize_system()
    try:
        # Use crypto portfolio as primary data source
        if crypto_portfolio:
            summary = crypto_portfolio.get_portfolio_summary()
            chart_data = crypto_portfolio.get_portfolio_chart_data(hours=24)
            
            return {
                "total_value": summary["total_current_value"],
                "cash": summary["total_current_value"] * 0.1,  # Assume 10% cash
                "positions_value": summary["total_current_value"] * 0.9,  # 90% in positions
                "daily_pnl": summary["total_pnl"],
                "total_return": summary["total_pnl_percent"] / 100,
                "chart_data": chart_data,
            }
        
        # Fallback to trading system portfolio
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

        # Get portfolio history for charts
        portfolio_history = db_manager.get_portfolio_history(mode=trading_status["mode"], days=7)
        if not portfolio_history.empty:
            chart_data = [{"timestamp": row["timestamp"].isoformat(), "value": row["total_value"]} for _, row in portfolio_history.iterrows()]
        else:
            # If no history, create sample data points to show current portfolio value
            current_time = datetime.now()
            chart_data = [
                {"timestamp": (current_time - timedelta(hours=6)).isoformat(), "value": portfolio_value},
                {"timestamp": (current_time - timedelta(hours=3)).isoformat(), "value": portfolio_value},
                {"timestamp": current_time.isoformat(), "value": portfolio_value}
            ]

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

        # Clean up infinite and NaN values for JSON serialization
        cleaned_results = {}
        for key, value in results.items():
            if isinstance(value, float):
                import math
                if math.isinf(value) or math.isnan(value):
                    if key in ['profit_factor', 'sharpe_ratio']:
                        cleaned_results[key] = 0.0  # Set to 0 for ratios
                    else:
                        cleaned_results[key] = 0.0
                else:
                    cleaned_results[key] = round(value, 6)  # Round to 6 decimal places
            else:
                cleaned_results[key] = value

        performance_data = {
            "strategy_name": "BollingerBands",
            "symbol": symbol,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "total_return": cleaned_results.get("total_return", 0),
            "sharpe_ratio": cleaned_results.get("sharpe_ratio", 0),
            "max_drawdown": cleaned_results.get("max_drawdown", 0),
            "total_trades": cleaned_results.get("total_trades", 0),
            "win_rate": cleaned_results.get("win_rate", 0),
            "mode": "backtest",
        }
        db_manager.save_strategy_performance(performance_data)
        
        # Store backtest results in global status for frontend display
        global backtest_results
        backtest_results = cleaned_results
        
        return jsonify({"success": True, "results": cleaned_results})
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
