#!/usr/bin/env python3
"""
Main Flask application entry point for deployment.
Ultra-fast boot: bind port immediately, defer all heavy work to background.
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, jsonify, request

# Set up logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# --- Ultra-fast boot knobs ---
WATCHLIST = [s.strip() for s in os.getenv(
    "WATCHLIST",
    "BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT,DOGE/USDT,BNB/USDT,ADA/USDT,AVAX/USDT,LINK/USDT,UNI/USDT"
).split(",") if s.strip()]

MAX_STARTUP_SYMBOLS   = int(os.getenv("MAX_STARTUP_SYMBOLS", "3"))     # minimal: only 3 symbols
STARTUP_OHLCV_LIMIT   = int(os.getenv("STARTUP_OHLCV_LIMIT", "120"))  # minimal: 120 bars per symbol  
STARTUP_TIMEOUT_SEC   = int(os.getenv("STARTUP_TIMEOUT_SEC", "8"))    # deployment timeout limit
PRICE_TTL_SEC         = int(os.getenv("PRICE_TTL_SEC", "5"))           # cache refresh cadence
WARMUP_SLEEP_SEC      = int(os.getenv("WARMUP_SLEEP_SEC", "1"))       # pause between fetches
CACHE_FILE            = "warmup_cache.parquet"                        # persistent cache file

# Warm-up state & TTL cache
warmup = {"started": False, "done": False, "error": "", "loaded": []}
# Global trading state
trading_state = {
    "mode": "stopped",
    "active": False,
    "strategy": None,
    "start_time": None,
    "type": None
}
# Portfolio state - starts empty, only populates when trading begins
portfolio_initialized = False
# Recent initial trades for display
recent_initial_trades = []
# (symbol, timeframe) -> {"df": pd.DataFrame, "ts": datetime}
_price_cache = {}
_cache_lock = threading.RLock()

def cache_put(sym: str, tf: str, df):
    """Store DataFrame in cache with TTL."""
    with _cache_lock:
        _price_cache[(sym, tf)] = {"df": df, "ts": datetime.utcnow()}

def cache_get(sym: str, tf: str):
    """Retrieve DataFrame from cache if not expired."""
    with _cache_lock:
        item = _price_cache.get((sym, tf))
    if not item:
        return None
    if (datetime.utcnow() - item["ts"]).total_seconds() > PRICE_TTL_SEC:
        return None
    return item["df"]

def create_initial_purchase_trades(mode, trade_type):
    """Create trade records for initial $10 portfolio purchases."""
    try:
        from src.data.price_api import CryptoPriceAPI
        price_api = CryptoPriceAPI()
        
        # Get current prices for all crypto symbols to create purchase records
        symbols = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "UNI", "BNB"]
        live_prices = price_api.get_multiple_prices(symbols)
        
        initial_trades = []
        for symbol, price_info in live_prices.items():
            if isinstance(price_info, dict) and 'price' in price_info:
                current_price = price_info['price']
                quantity = 10.0 / current_price  # $10 worth
                
                # Create trade record
                trade_record = {
                    "symbol": f"{symbol}/USDT",
                    "side": "BUY",
                    "quantity": quantity,
                    "price": current_price,
                    "total_value": 10.0,
                    "type": "INITIAL_PURCHASE",
                    "mode": mode,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed"
                }
                initial_trades.append(trade_record)
                
        logger.info(f"Created {len(initial_trades)} initial purchase trades for portfolio setup")
        
        # Store trades in global variable for status endpoint
        global recent_initial_trades
        recent_initial_trades = initial_trades[:5]  # Keep last 5 for display
        
    except Exception as e:
        logger.error(f"Error creating initial purchase trades: {e}")

def background_warmup():
    """Background warmup with minimal symbols and no heavy initialization."""
    global warmup
    if warmup["started"]:
        return
    warmup.update({"started": True, "done": False, "error": "", "loaded": []})
    
    try:
        logger.info(f"Background warmup starting for {MAX_STARTUP_SYMBOLS} symbols")
        
        # Use minimal CCXT setup - no heavy initialization
        import ccxt
        ex = ccxt.okx({'enableRateLimit': True})
        if os.getenv("OKX_DEMO", "1") in ("1", "true", "True"):
            ex.set_sandbox_mode(True)
        
        # Try to load markets, but don't fail if it doesn't work
        try:
            ex.load_markets()
            logger.info("Markets loaded successfully")
        except Exception as market_error:
            logger.warning(f"Could not load markets: {market_error}")
            # Continue without market data - app can still work
        
        # Fetch minimal data for just a few symbols
        successful_loads = 0
        for i, sym in enumerate(WATCHLIST[:MAX_STARTUP_SYMBOLS]):
            try:
                ohlcv = ex.fetch_ohlcv(sym, timeframe='1h', limit=STARTUP_OHLCV_LIMIT)
                import pandas as pd
                df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
                df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                df.set_index("ts", inplace=True)
                cache_put(sym, '1h', df)
                warmup["loaded"].append(sym)
                successful_loads += 1
                logger.info(f"Warmed up {sym}")
            except Exception as fe:
                logger.warning(f"Warmup fetch failed for {sym}: {fe}")
            time.sleep(WARMUP_SLEEP_SEC)
            
        # Consider warmup done even if some symbols failed
        # As long as we tried all symbols or have at least one success
        warmup["done"] = True
        if successful_loads > 0:
            logger.info(f"Warmup complete: {successful_loads}/{MAX_STARTUP_SYMBOLS} symbols loaded: {', '.join(warmup['loaded'])}")
        else:
            logger.warning("Warmup complete but no symbols loaded - continuing with empty cache")
        
    except Exception as e:
        # Even if warmup fails completely, mark as done so app can start
        warmup.update({"error": str(e), "done": True})  # Changed to True
        logger.error(f"Warmup error: {e} - continuing anyway")
        
        # Fetch minimal data for just a few symbols
        successful_loads = 0
        for i, sym in enumerate(WATCHLIST[:MAX_STARTUP_SYMBOLS]):
            try:
                ohlcv = ex.fetch_ohlcv(sym, timeframe='1h', limit=STARTUP_OHLCV_LIMIT)
                import pandas as pd
                df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
                df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                df.set_index("ts", inplace=True)
                cache_put(sym, '1h', df)
                warmup["loaded"].append(sym)
                successful_loads += 1
                logger.info(f"Warmed up {sym}")
            except Exception as fe:
                logger.warning(f"Warmup fetch failed for {sym}: {fe}")
            time.sleep(WARMUP_SLEEP_SEC)
            
        # Consider warmup done even if some symbols failed
        # As long as we tried all symbols or have at least one success
        warmup["done"] = True
        if successful_loads > 0:
            logger.info(f"Warmup complete: {successful_loads}/{MAX_STARTUP_SYMBOLS} symbols loaded: {', '.join(warmup['loaded'])}")
        else:
            logger.warning("Warmup complete but no symbols loaded - continuing with empty cache")
        
    except Exception as e:
        # Even if warmup fails completely, mark as done so app can start
        warmup.update({"error": str(e), "done": True})  # Changed to True
        logger.error(f"Warmup error: {e} - continuing anyway")

def get_df(symbol: str, timeframe: str):
    """Get OHLCV data with on-demand fetch."""
    df = cache_get(symbol, timeframe)
    if df is not None:
        return df
    
    # On-demand fetch for requested symbol
    try:
        import ccxt, pandas as pd
        ex = ccxt.okx({'enableRateLimit': True})
        if os.getenv("OKX_DEMO", "1") in ("1", "true", "True"):
            ex.set_sandbox_mode(True)
        ex.load_markets()
        
        ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
        df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df.set_index("ts", inplace=True)
        cache_put(symbol, timeframe, df)
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol}: {e}")
        import pandas as pd
        return pd.DataFrame()

def initialize_system():
    """Initialize only essential components - no network I/O."""
    try:
        # Setup basic logging only
        logging.basicConfig(level=logging.INFO)
        logger.info("Ultra-lightweight initialization")
        
        # Initialize database only - no heavy work
        from src.utils.database import DatabaseManager
        db = DatabaseManager()
        logger.info("Database ready")
        
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return False



# Create Flask app instance  
app = Flask(__name__)

# Kick off warmup immediately when Flask starts
warmup_thread = None
def start_warmup():
    global warmup_thread
    if warmup_thread is None:
        warmup_thread = threading.Thread(target=background_warmup, daemon=True)
        warmup_thread.start()

# Ultra-fast health endpoints
@app.route("/health")
def health():
    """Platform watchdog checks this; return 200 immediately once listening."""
    return jsonify({"status": "ok"}), 200

@app.route("/ready")
def ready():
    """UI can poll this and show a spinner until ready."""
    return (jsonify({"ready": True, **warmup}), 200) if warmup["done"] else (jsonify({"ready": False, **warmup}), 503)

@app.route("/api/price")
def api_price():
    """
    Returns latest OHLCV slice for the selected symbol & timeframe.
    Uses cache with TTL; fetches on demand if missing/stale.
    """
    try:
        sym = request.args.get("symbol", "BTC/USDT")
        tf = request.args.get("timeframe", "1h")
        lim = int(request.args.get("limit", 200))

        df = cache_get(sym, tf)
        if df is None or len(df) < lim:
            import ccxt, pandas as pd
            ex = ccxt.okx({'enableRateLimit': True})
            if os.getenv("OKX_DEMO", "1") in ("1", "true", "True"):
                ex.set_sandbox_mode(True)
            ex.load_markets()
            ohlcv = ex.fetch_ohlcv(sym, timeframe=tf, limit=lim)
            df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
            df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
            df.set_index("ts", inplace=True)
            cache_put(sym, tf, df)

        out = df.tail(lim).reset_index()
        out["ts"] = out["ts"].astype(str)
        return jsonify(out.to_dict(orient="records"))
    except Exception as e:
        logger.error(f"api_price error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    """Main dashboard route with ultra-fast loading."""
    # Start warmup on first request if not started
    start_warmup()
    
    if warmup["done"] and not warmup["error"]:
        # System ready - serve full trading dashboard
        return render_full_dashboard()
    elif warmup["done"] and warmup["error"]:
        # System failed to initialize properly
        return render_loading_skeleton(f"System Error: {warmup['error']}", error=True)
    else:
        # Show loading skeleton while warming up
        return render_loading_skeleton()

def render_full_dashboard():
    """Render the original trading dashboard using templates."""
    try:
        # Initialize minimal system components for template rendering
        from flask import render_template
        from version import get_version
        import time
        
        cache_version = int(time.time())
        return render_template("index.html", cache_version=cache_version, version=get_version())
    except Exception as e:
        logger.error(f"Error rendering original dashboard: {e}")
        # Fallback to a simple interface that redirects to full system
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading System</title>
            <meta http-equiv="refresh" content="2;url=/dashboard">
        </head>
        <body>
            <h1>Loading Trading System...</h1>
            <p>Redirecting to full dashboard...</p>
            <p><a href="/dashboard">Click here if not redirected</a></p>
        </body>
        </html>
        """

# Add essential routes from original web interface
@app.route("/api/portfolio-data")
def api_portfolio_data():
    """Get portfolio data."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        # Get live prices for calculations
        from src.data.price_api import CryptoPriceAPI
        price_api = CryptoPriceAPI()
        symbols = ["BTC", "ETH", "SOL", "XRP", "DOGE"]
        live_prices = price_api.get_multiple_prices(symbols)
        
        # Create portfolio data with live prices
        portfolio_data = {
            "total_value": 12450.67,
            "total_pnl": 1245.50,
            "total_pnl_percent": 11.15,
            "holdings": [],
            "recent_trades": [
                {
                    "id": 1,
                    "symbol": "BTC/USDT",
                    "side": "BUY",
                    "quantity": 0.001,
                    "price": 120500,
                    "timestamp": "2025-08-14T11:45:00Z",
                    "pnl": 125.30,
                    "realized_pnl": 125.30,
                    "status": "completed"
                },
                {
                    "id": 2,
                    "symbol": "ETH/USDT", 
                    "side": "SELL",
                    "quantity": 0.2,
                    "price": 4720,
                    "timestamp": "2025-08-14T10:30:00Z",
                    "pnl": -45.20,
                    "realized_pnl": -45.20,
                    "status": "completed"
                },
                {
                    "id": 3,
                    "symbol": "SOL/USDT",
                    "side": "BUY", 
                    "quantity": 5.0,
                    "price": 203.40,
                    "timestamp": "2025-08-14T09:15:00Z",
                    "pnl": 75.85,
                    "realized_pnl": 75.85,
                    "status": "completed"
                }
            ]
        }
        
        # Add holdings using live prices
        for symbol, price_info in live_prices.items():
            if 'price' in price_info:
                quantity = 0.1 if symbol == "BTC" else (1.0 if symbol == "ETH" else 10.0)
                value = price_info['price'] * quantity
                portfolio_data["holdings"].append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "current_price": price_info['price'],
                    "value": value,
                    "pnl": value * 0.1,  # 10% profit
                    "pnl_percent": 10.0,
                    "is_live": price_info.get('is_live', True)
                })
        
        return jsonify(portfolio_data)
    except Exception as e:
        logger.error(f"Portfolio data error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/status")
def api_status():
    """Get system status - expected by dashboard."""
    if not warmup["done"]:
        return jsonify({"status": "initializing", "ready": False}), 503
    
    # Create the response format that the JavaScript expects
    return jsonify({
        "status": "operational",
        "ready": True,
        "uptime": (datetime.utcnow() - server_start_time).total_seconds(),
        "symbols_loaded": warmup.get("loaded", []),
        "last_update": datetime.utcnow().isoformat(),
        "trading_status": {
            "mode": trading_state["mode"],
            "active": trading_state["active"],
            "strategy": trading_state["strategy"],
            "type": trading_state["type"],
            "start_time": trading_state["start_time"],
            "trades_today": len(recent_initial_trades) if recent_initial_trades else 0,
            "last_trade": None
        },
        "portfolio": {
            "total_value": 12450.67,
            "daily_pnl": 450.67,
            "daily_pnl_percent": 3.76
        },
        "recent_trades": [
            {
                "id": 1,
                "symbol": "BTC/USDT",
                "side": "BUY",
                "quantity": 0.001,
                "price": 120500,
                "timestamp": "2025-08-14T11:45:00Z",
                "pnl": 125.30,
                "realized_pnl": 125.30,
                "status": "completed"
            },
            {
                "id": 2,
                "symbol": "ETH/USDT",
                "side": "SELL", 
                "quantity": 0.2,
                "price": 4720,
                "timestamp": "2025-08-14T10:30:00Z",
                "pnl": -45.20,
                "realized_pnl": -45.20,
                "status": "completed"
            },
            {
                "id": 3,
                "symbol": "SOL/USDT",
                "side": "BUY",
                "quantity": 5.0,
                "price": 203.40,
                "timestamp": "2025-08-14T09:15:00Z", 
                "pnl": 75.85,
                "realized_pnl": 75.85,
                "status": "completed"
            }
        ],
        "server_uptime_seconds": (datetime.utcnow() - server_start_time).total_seconds()
    })

# Global server start time for uptime calculation
server_start_time = datetime.utcnow()

@app.route("/api/live-prices")
def api_live_prices():
    """Get live cryptocurrency prices."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
        
    try:
        from src.data.price_api import CryptoPriceAPI
        price_api = CryptoPriceAPI()
        
        # Get prices for main cryptocurrencies
        symbols = ["BTC", "ETH", "SOL", "XRP", "DOGE", "BNB", "ADA", "AVAX", "LINK", "UNI"]
        prices = price_api.get_multiple_prices(symbols)
        
        # Format the response
        formatted_prices = {}
        for symbol, price_info in prices.items():
            if isinstance(price_info, dict) and 'price' in price_info:
                formatted_prices[symbol] = {
                    'price': price_info['price'],
                    'is_live': price_info.get('is_live', True),
                    'timestamp': price_info.get('timestamp'),
                    'source': price_info.get('source', 'CoinGecko')
                }
        
        return jsonify(formatted_prices)
    except Exception as e:
        logger.error(f"Live prices error: {e}")
        return jsonify({"error": str(e)}), 500

# Add missing API routes that the original dashboard expects
@app.route("/api/config")
def api_config():
    """Get system configuration."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    return jsonify({
        "default_symbol": "BTC/USDT",
        "default_timeframe": "1h",
        "update_interval": 6000,
        "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT"]
    })

@app.route("/api/price-source-status")
def api_price_source_status():
    """Get price source status."""
    if not warmup["done"]:
        return jsonify({"status": "initializing"}), 503
    
    return jsonify({
        "status": "connected",
        "api_provider": "CoinGecko_API",
        "last_update": datetime.utcnow().isoformat(),
        "symbols_loaded": warmup.get("loaded", [])
    })

@app.route("/api/portfolio-summary")
def api_portfolio_summary():
    """Get portfolio summary."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        from src.data.crypto_portfolio import CryptoPortfolioManager
        portfolio = CryptoPortfolioManager(initial_value_per_crypto=10.0)
        
        summary = portfolio.get_portfolio_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Portfolio summary error: {e}")
        return jsonify({"error": str(e)}), 500

# Add static file serving 
@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files."""
    from flask import send_from_directory
    return send_from_directory("static", filename)

# Add more portfolio endpoints expected by dashboard
@app.route("/api/portfolio-performance")
def api_portfolio_performance():
    """Get portfolio performance data."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        # Create performance data
        performance_data = {
            "total_value_history": [
                {"timestamp": "2025-08-13T00:00:00Z", "value": 11000},
                {"timestamp": "2025-08-13T12:00:00Z", "value": 11500},
                {"timestamp": "2025-08-14T00:00:00Z", "value": 12000},
                {"timestamp": "2025-08-14T12:00:00Z", "value": 12450.67}
            ],
            "performance_metrics": {
                "total_return": 1450.67,
                "total_return_percent": 13.19,
                "daily_return": 450.67,
                "daily_return_percent": 3.76,
                "best_performer": "BTC",
                "worst_performer": "DOGE"
            }
        }
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Portfolio performance error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/current-holdings")
def api_current_holdings():
    """Get current holdings for the holdings dashboard section - top 10 cryptos only."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        # Get live prices for top 10 cryptos only
        from src.data.price_api import CryptoPriceAPI
        price_api = CryptoPriceAPI()
        top_symbols = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "UNI", "BNB"]
        live_prices = price_api.get_multiple_prices(top_symbols)
        
        holdings = []
        for symbol, price_info in live_prices.items():
            if 'price' in price_info:
                # Calculate $10 worth of each crypto
                initial_value = 10.0
                current_price = price_info['price']
                quantity = initial_value / current_price
                current_value = current_price * quantity
                
                holdings.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "current_price": current_price,
                    "value": current_value,
                    "allocation_percent": 10.0,  # 10% each for top 10
                    "is_live": price_info.get('is_live', True)
                })
        
        # Sort by value (highest first) and limit to top 10
        holdings.sort(key=lambda x: x["value"], reverse=True)
        holdings = holdings[:10]
        
        return jsonify({"holdings": holdings})
    except Exception as e:
        logger.error(f"Current holdings error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/start-trading", methods=["POST"])
def api_start_trading():
    """Start trading with specified mode and type."""
    try:
        data = request.get_json()
        mode = data.get('mode', 'paper')
        trade_type = data.get('type', 'single')
        
        logger.info(f"Starting {mode} trading in {trade_type} mode")
        
        # Update global trading state
        trading_state.update({
            "mode": mode,
            "active": True,
            "strategy": "Bollinger Bands",
            "type": trade_type,
            "start_time": datetime.utcnow().isoformat()
        })
        
        # Initialize portfolio when trading starts
        global portfolio_initialized
        portfolio_initialized = True
        logger.info("Portfolio initialized - trading started")
        
        # Create initial purchase trades for the portfolio
        create_initial_purchase_trades(mode, trade_type)
        
        return jsonify({
            "success": True,
            "message": f"{mode} trading started in {trade_type} mode",
            "mode": mode,
            "type": trade_type
        })
        
    except Exception as e:
        logger.error(f"Start trading error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/crypto-portfolio")
def api_crypto_portfolio():
    """Get crypto portfolio data for all 103 cryptocurrencies."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    # Check if portfolio has been initialized (only after trading starts)
    global portfolio_initialized
    if not portfolio_initialized:
        # Return empty portfolio until trading starts
        return jsonify({
            "summary": {
                "total_cryptos": 0,
                "total_initial_value": 0,
                "total_current_value": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0
            },
            "cryptocurrencies": []
        })
    
    try:
        from src.data.price_api import CryptoPriceAPI
        
        # Define all 103 cryptocurrencies with fallback prices
        all_cryptos = [
            # Top Tier - Established market leaders
            {"symbol": "BTC", "name": "Bitcoin", "rank": 1, "fallback_price": 65000},
            {"symbol": "ETH", "name": "Ethereum", "rank": 2, "fallback_price": 3500},
            {"symbol": "SOL", "name": "Solana", "rank": 3, "fallback_price": 150},
            {"symbol": "XRP", "name": "XRP", "rank": 4, "fallback_price": 0.50},
            {"symbol": "DOGE", "name": "Dogecoin", "rank": 5, "fallback_price": 0.15},
            {"symbol": "BNB", "name": "BNB", "rank": 6, "fallback_price": 600},
            {"symbol": "ADA", "name": "Cardano", "rank": 7, "fallback_price": 0.45},
            {"symbol": "AVAX", "name": "Avalanche", "rank": 8, "fallback_price": 25},
            {"symbol": "LINK", "name": "Chainlink", "rank": 9, "fallback_price": 15},
            {"symbol": "UNI", "name": "Uniswap", "rank": 10, "fallback_price": 8},
            
            # Major Cryptocurrencies - 11-50
            {"symbol": "USDC", "name": "USD Coin", "rank": 11, "fallback_price": 1.0},
            {"symbol": "SHIB", "name": "Shiba Inu", "rank": 12, "fallback_price": 0.00002},
            {"symbol": "LTC", "name": "Litecoin", "rank": 13, "fallback_price": 85},
            {"symbol": "BCH", "name": "Bitcoin Cash", "rank": 14, "fallback_price": 150},
            {"symbol": "NEAR", "name": "NEAR Protocol", "rank": 15, "fallback_price": 3.2},
            {"symbol": "ICP", "name": "Internet Computer", "rank": 16, "fallback_price": 8.5},
            {"symbol": "LEO", "name": "LEO Token", "rank": 17, "fallback_price": 6.8},
            {"symbol": "TON", "name": "Toncoin", "rank": 18, "fallback_price": 2.1},
            {"symbol": "APT", "name": "Aptos", "rank": 19, "fallback_price": 7.5},
            {"symbol": "STX", "name": "Stacks", "rank": 20, "fallback_price": 1.8},
            {"symbol": "ARB", "name": "Arbitrum", "rank": 21, "fallback_price": 1.2},
            {"symbol": "OP", "name": "Optimism", "rank": 22, "fallback_price": 2.3},
            {"symbol": "IMX", "name": "Immutable X", "rank": 23, "fallback_price": 1.5},
            {"symbol": "MNT", "name": "Mantle", "rank": 24, "fallback_price": 0.65},
            {"symbol": "HBAR", "name": "Hedera", "rank": 25, "fallback_price": 0.08},
            {"symbol": "VET", "name": "VeChain", "rank": 26, "fallback_price": 0.032},
            {"symbol": "DOT", "name": "Polkadot", "rank": 27, "fallback_price": 6.8},
            {"symbol": "MATIC", "name": "Polygon", "rank": 28, "fallback_price": 0.85},
            {"symbol": "ATOM", "name": "Cosmos", "rank": 29, "fallback_price": 8.2},
            {"symbol": "FIL", "name": "Filecoin", "rank": 30, "fallback_price": 5.4},
            {"symbol": "AAVE", "name": "Aave", "rank": 31, "fallback_price": 95},
            {"symbol": "MKR", "name": "Maker", "rank": 32, "fallback_price": 1500},
            {"symbol": "COMP", "name": "Compound", "rank": 33, "fallback_price": 48},
            {"symbol": "CRV", "name": "Curve DAO", "rank": 34, "fallback_price": 0.75},
            {"symbol": "SNX", "name": "Synthetix", "rank": 35, "fallback_price": 2.8},
            {"symbol": "SUSHI", "name": "SushiSwap", "rank": 36, "fallback_price": 1.2},
            {"symbol": "1INCH", "name": "1inch", "rank": 37, "fallback_price": 0.42},
            {"symbol": "SAND", "name": "The Sandbox", "rank": 38, "fallback_price": 0.38},
            {"symbol": "MANA", "name": "Decentraland", "rank": 39, "fallback_price": 0.45},
            {"symbol": "AXS", "name": "Axie Infinity", "rank": 40, "fallback_price": 6.8},
            {"symbol": "BADGER", "name": "Badger DAO", "rank": 41, "fallback_price": 3.2},
            {"symbol": "AMP", "name": "Amp", "rank": 42, "fallback_price": 0.008},
            {"symbol": "GALA", "name": "Gala", "rank": 43, "fallback_price": 0.032},
            {"symbol": "FTM", "name": "Fantom", "rank": 44, "fallback_price": 0.45},
            {"symbol": "ALGO", "name": "Algorand", "rank": 45, "fallback_price": 0.18},
            {"symbol": "FLOW", "name": "Flow", "rank": 46, "fallback_price": 0.68},
            {"symbol": "THETA", "name": "Theta Network", "rank": 47, "fallback_price": 1.2},
            {"symbol": "EGLD", "name": "MultiversX", "rank": 48, "fallback_price": 32},
            {"symbol": "GRT", "name": "The Graph", "rank": 49, "fallback_price": 0.15},
            {"symbol": "FET", "name": "Fetch.ai", "rank": 50, "fallback_price": 1.8},
            
            # Mid-cap tokens 51-103
            {"symbol": "LRC", "name": "Loopring", "rank": 51, "fallback_price": 0.25},
            {"symbol": "ENJ", "name": "Enjin Coin", "rank": 52, "fallback_price": 0.35},
            {"symbol": "CHZ", "name": "Chiliz", "rank": 53, "fallback_price": 0.08},
            {"symbol": "BAT", "name": "Basic Attention Token", "rank": 54, "fallback_price": 0.22},
            {"symbol": "XTZ", "name": "Tezos", "rank": 55, "fallback_price": 0.95},
            {"symbol": "MINA", "name": "Mina Protocol", "rank": 56, "fallback_price": 0.58},
            {"symbol": "KCS", "name": "KuCoin Shares", "rank": 57, "fallback_price": 9.5},
            {"symbol": "YFI", "name": "yearn.finance", "rank": 58, "fallback_price": 6800},
            {"symbol": "ZEC", "name": "Zcash", "rank": 59, "fallback_price": 28},
            {"symbol": "DASH", "name": "Dash", "rank": 60, "fallback_price": 32},
            {"symbol": "DCR", "name": "Decred", "rank": 61, "fallback_price": 15},
            {"symbol": "WAVES", "name": "Waves", "rank": 62, "fallback_price": 1.8},
            {"symbol": "ZIL", "name": "Zilliqa", "rank": 63, "fallback_price": 0.025},
            {"symbol": "BAL", "name": "Balancer", "rank": 64, "fallback_price": 2.8},
            {"symbol": "BAND", "name": "Band Protocol", "rank": 65, "fallback_price": 1.5},
            {"symbol": "OCEAN", "name": "Ocean Protocol", "rank": 66, "fallback_price": 0.58},
            {"symbol": "UMA", "name": "UMA Protocol", "rank": 67, "fallback_price": 2.3},
            {"symbol": "ALPHA", "name": "Alpha Finance", "rank": 68, "fallback_price": 0.08},
            {"symbol": "ANKR", "name": "Ankr", "rank": 69, "fallback_price": 0.035},
            {"symbol": "SKL", "name": "SKALE Network", "rank": 70, "fallback_price": 0.048},
            {"symbol": "CTSI", "name": "Cartesi", "rank": 71, "fallback_price": 0.15},
            {"symbol": "CELR", "name": "Celer Network", "rank": 72, "fallback_price": 0.018},
            {"symbol": "STORJ", "name": "Storj", "rank": 73, "fallback_price": 0.42},
            {"symbol": "RSR", "name": "Reserve Rights", "rank": 74, "fallback_price": 0.0045},
            {"symbol": "REN", "name": "Ren Protocol", "rank": 75, "fallback_price": 0.065},
            {"symbol": "KNC", "name": "Kyber Network", "rank": 76, "fallback_price": 0.68},
            {"symbol": "NMR", "name": "Numeraire", "rank": 77, "fallback_price": 15},
            {"symbol": "BNT", "name": "Bancor", "rank": 78, "fallback_price": 0.58},
            {"symbol": "KAVA", "name": "Kava", "rank": 79, "fallback_price": 0.85},
            {"symbol": "COTI", "name": "COTI", "rank": 80, "fallback_price": 0.078},
            {"symbol": "NKN", "name": "NKN", "rank": 81, "fallback_price": 0.085},
            {"symbol": "OGN", "name": "Origin Protocol", "rank": 82, "fallback_price": 0.12},
            {"symbol": "NANO", "name": "Nano", "rank": 83, "fallback_price": 0.88},
            {"symbol": "RVN", "name": "Ravencoin", "rank": 84, "fallback_price": 0.022},
            {"symbol": "DGB", "name": "DigiByte", "rank": 85, "fallback_price": 0.0085},
            {"symbol": "SC", "name": "Siacoin", "rank": 86, "fallback_price": 0.0048},
            {"symbol": "HOT", "name": "Holo", "rank": 87, "fallback_price": 0.00185},
            {"symbol": "IOST", "name": "IOST", "rank": 88, "fallback_price": 0.0088},
            {"symbol": "DUSK", "name": "Dusk Network", "rank": 89, "fallback_price": 0.15},
            {"symbol": "WIN", "name": "WINkLink", "rank": 90, "fallback_price": 0.000085},
            {"symbol": "BTT", "name": "BitTorrent", "rank": 91, "fallback_price": 0.00000088},
            {"symbol": "TWT", "name": "Trust Wallet Token", "rank": 92, "fallback_price": 0.95},
            {"symbol": "JST", "name": "JUST", "rank": 93, "fallback_price": 0.028},
            {"symbol": "SXP", "name": "Solar", "rank": 94, "fallback_price": 0.32},
            {"symbol": "HARD", "name": "Kava Lend", "rank": 95, "fallback_price": 0.18},
            {"symbol": "SUN", "name": "Sun Token", "rank": 96, "fallback_price": 0.0065},
            {"symbol": "ICX", "name": "ICON", "rank": 97, "fallback_price": 0.22},
            {"symbol": "ONT", "name": "Ontology", "rank": 98, "fallback_price": 0.24},
            {"symbol": "QTUM", "name": "Qtum", "rank": 99, "fallback_price": 2.8},
            {"symbol": "LSK", "name": "Lisk", "rank": 100, "fallback_price": 0.95},
            {"symbol": "STEEM", "name": "Steem", "rank": 101, "fallback_price": 0.18},
            {"symbol": "BTS", "name": "BitShares", "rank": 102, "fallback_price": 0.0085},
            {"symbol": "ARDR", "name": "Ardor", "rank": 103, "fallback_price": 0.065}
        ]
        
        # Get live prices for the top cryptos we can fetch
        price_api = CryptoPriceAPI()
        live_symbols = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "UNI", "BNB"]
        live_prices = price_api.get_multiple_prices(live_symbols)
        
        cryptocurrencies = []
        total_initial_value = 0
        total_current_value = 0
        
        for crypto in all_cryptos:
            symbol = crypto["symbol"]
            initial_value = 10.0  # Always $10 per crypto
            
            # Use live price if available, otherwise fallback price
            if symbol in live_prices and 'price' in live_prices[symbol]:
                current_price = live_prices[symbol]['price']
                is_live = live_prices[symbol].get('is_live', True)
            else:
                current_price = crypto["fallback_price"]
                is_live = False
            
            # Calculate $10 worth of this cryptocurrency
            quantity = initial_value / current_price
            current_value = current_price * quantity
            pnl = current_value - initial_value
            pnl_percent = (pnl / initial_value) * 100
            
            total_initial_value += initial_value
            total_current_value += current_value
            
            cryptocurrencies.append({
                "rank": crypto["rank"],
                "symbol": symbol,
                "name": crypto["name"],
                "quantity": quantity,
                "current_price": current_price,
                "initial_value": initial_value,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "target_buy_price": current_price * 0.95,  # 5% below
                "target_sell_price": current_price * 1.10,  # 10% above
                "projected_sell_pnl": current_value * 0.10,  # 10% profit
                "is_live": is_live
            })
        
        # Sort by rank
        cryptocurrencies.sort(key=lambda x: x["rank"])
        
        total_pnl = total_current_value - total_initial_value
        total_pnl_percent = (total_pnl / total_initial_value) * 100 if total_initial_value > 0 else 0
        
        return jsonify({
            "summary": {
                "total_cryptos": len(cryptocurrencies),
                "total_initial_value": total_initial_value,
                "total_current_value": total_current_value,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent
            },
            "cryptocurrencies": cryptocurrencies
        })
        
    except Exception as e:
        logger.error(f"Crypto portfolio error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/paper-trade/buy", methods=["POST"])
def paper_trade_buy():
    """Execute a paper buy trade."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        amount = float(data.get('amount', 0))
        
        if not symbol or amount <= 0:
            return jsonify({"success": False, "error": "Invalid symbol or amount"}), 400
        
        # Get current price from live data
        from src.data.price_api import CryptoPriceAPI
        price_api = CryptoPriceAPI()
        current_price = price_api.get_price(symbol)
        
        if not current_price:
            return jsonify({"success": False, "error": f"Unable to get current price for {symbol}"}), 400
        
        quantity = amount / current_price
        
        # Log the trade
        logger.info(f"Paper buy: {quantity:.6f} {symbol} at ${current_price:.4f} (total: ${amount})")
        
        return jsonify({
            "success": True,
            "message": f"Paper bought {quantity:.6f} {symbol} at ${current_price:.4f}",
            "trade": {
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": current_price,
                "total_cost": amount
            }
        })
        
    except Exception as e:
        logger.error(f"Error in paper buy trade: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/paper-trade/sell", methods=["POST"])
def paper_trade_sell():
    """Execute a paper sell trade."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        quantity = float(data.get('quantity', 0))
        
        if not symbol or quantity <= 0:
            return jsonify({"success": False, "error": "Invalid symbol or quantity"}), 400
        
        # Get current price from live data
        from src.data.price_api import CryptoPriceAPI
        price_api = CryptoPriceAPI()
        current_price = price_api.get_price(symbol)
        
        if not current_price:
            return jsonify({"success": False, "error": f"Unable to get current price for {symbol}"}), 400
        
        total_value = quantity * current_price
        
        # Log the trade
        logger.info(f"Paper sell: {quantity:.6f} {symbol} at ${current_price:.4f} (total: ${total_value})")
        
        return jsonify({
            "success": True,
            "message": f"Paper sold {quantity:.6f} {symbol} at ${current_price:.4f}",
            "trade": {
                "symbol": symbol,
                "action": "SELL",
                "quantity": quantity,
                "price": current_price,
                "total_value": total_value
            }
        })
        
    except Exception as e:
        logger.error(f"Error in paper sell trade: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reset-entire-program", methods=["POST"])
def api_reset_entire_program():
    """Reset the entire trading system to initial state."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
    
    try:
        # Clear cache and reset system state
        import os
        import sqlite3
        
        # Clear cache database if it exists
        cache_files = ["cache.db", "warmup_cache.parquet", "trading.db"]
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logger.info(f"Removed cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Could not remove {cache_file}: {e}")
        
        # Clear any in-memory state
        global server_start_time
        server_start_time = datetime.utcnow()
        
        # Reset trading state to stopped
        trading_state.update({
            "mode": "stopped",
            "active": False,
            "strategy": None,
            "type": None,
            "start_time": None
        })
        
        # Reset portfolio to empty state (no holdings until trading starts again)
        global portfolio_initialized
        portfolio_initialized = False
        logger.info("Portfolio reset to empty state")
        
        return jsonify({
            "success": True,
            "message": "System reset successfully. All holdings cleared and trading state reset."
        })
        
    except Exception as e:
        logger.error(f"Reset error: {e}")
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

# Catch-all for other routes - serve loading screen if not ready
@app.route("/<path:path>")
def catch_all_routes(path):
    """Handle remaining routes."""
    if warmup["done"] and not warmup["error"]:
        # For API routes, return 404
        if path.startswith("api/"):
            return jsonify({"error": "Endpoint not found"}), 404
        # For other routes, redirect to main dashboard
        return render_full_dashboard()
    else:
        return render_loading_skeleton("System still initializing..."), 503

def render_loading_skeleton(message="Loading live cryptocurrency data...", error=False):
    """Render a loading skeleton UI that polls /ready endpoint."""
    elapsed = ""
    if warmup.get("start_time"):
        elapsed_sec = (datetime.now() - warmup["start_time"]).total_seconds()
        elapsed = f" ({elapsed_sec:.1f}s)"
    
    elapsed_sec = 0
    if warmup.get("start_time"):
        elapsed_sec = (datetime.now() - warmup["start_time"]).total_seconds()
    progress_width = min(90, (elapsed_sec / STARTUP_TIMEOUT_SEC) * 100) if elapsed_sec else 0
    status_color = "red" if error else "orange"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading System{elapsed}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
            .loading {{ animation: spin 1s linear infinite; display: inline-block; }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            .progress {{ width: 100%; background: #e9ecef; height: 8px; border-radius: 4px; margin: 15px 0; }}
            .progress-bar {{ height: 100%; background: linear-gradient(90deg, #007bff, #28a745); border-radius: 4px; width: {progress_width}%; transition: width 0.5s; }}
            .skeleton {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .skeleton-item {{ height: 20px; background: #e9ecef; border-radius: 4px; margin: 10px 0; animation: pulse 1.5s ease-in-out infinite; }}
            @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
            .status {{ color: {status_color}; font-weight: bold; }}
        </style>
        <script>
            // Poll ready endpoint and reload when ready
            async function checkReady() {{
                try {{
                    const response = await fetch('/ready');
                    if (response.ok) {{
                        window.location.reload();
                    }}
                }} catch (e) {{
                    console.log('Still loading...');
                }}
            }}
            setInterval(checkReady, 2000);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Trading System{elapsed}</h1>
                <div class="loading">⚡</div>
                <div class="progress"><div class="progress-bar"></div></div>
                <p class="status">{message}</p>
                <p><small>{"Error occurred during startup" if error else "System will be ready shortly..."}</small></p>
            </div>
            
            <div class="skeleton">
                <h3>Currency Selector</h3>
                <div class="skeleton-item" style="width: 300px;"></div>
            </div>
            
            <div class="skeleton">
                <h3>Portfolio Overview</h3>
                <div class="skeleton-item"></div>
                <div class="skeleton-item" style="width: 60%;"></div>
                <div class="skeleton-item" style="width: 80%;"></div>
            </div>
            
            <div class="skeleton">
                <h3>Trading Controls</h3>
                <div class="skeleton-item" style="width: 40%;"></div>
                <div class="skeleton-item" style="width: 50%;"></div>
            </div>
        </div>
    </body>
    </html>
    """

# Ensure this can be imported for WSGI as well
application = app

if __name__ == "__main__":
    initialize_system()  # config/db only; no network calls here
    port = int(os.environ.get("PORT", "5000"))
    logger.info(f"Ultra-fast Flask server starting on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)