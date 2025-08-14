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
PRICE_TTL_SEC         = int(os.getenv("PRICE_TTL_SEC", "5"))           # cache refresh cadence
WARMUP_SLEEP_SEC      = int(os.getenv("WARMUP_SLEEP_SEC", "1"))       # pause between fetches
CACHE_FILE            = "warmup_cache.parquet"                        # persistent cache file

# Warm-up state & TTL cache
warmup = {"started": False, "done": False, "error": "", "loaded": []}
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
        ex.load_markets()
        
        # Fetch minimal data for just a few symbols
        for i, sym in enumerate(WATCHLIST[:MAX_STARTUP_SYMBOLS]):
            try:
                ohlcv = ex.fetch_ohlcv(sym, timeframe='1h', limit=STARTUP_OHLCV_LIMIT)
                import pandas as pd
                df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
                df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                df.set_index("ts", inplace=True)
                cache_put(sym, '1h', df)
                warmup["loaded"].append(sym)
                logger.info(f"Warmed up {sym}")
            except Exception as fe:
                logger.warning(f"Warmup fetch failed for {sym}: {fe}")
            time.sleep(WARMUP_SLEEP_SEC)
            
        warmup["done"] = True
        logger.info(f"Warmup complete: {', '.join(warmup['loaded'])}")
        
    except Exception as e:
        warmup.update({"error": str(e), "done": False})
        logger.error(f"Warmup error: {e}")

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
        # Initialize crypto portfolio if needed
        from src.data.crypto_portfolio import CryptoPortfolioManager
        portfolio = CryptoPortfolioManager(initial_value_per_crypto=100.0)
        
        data = portfolio.get_portfolio_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Portfolio data error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/live-prices")
def api_live_prices():
    """Get live cryptocurrency prices."""
    if not warmup["done"]:
        return jsonify({"error": "System still initializing"}), 503
        
    try:
        from src.data.price_api import PriceAPI
        price_api = PriceAPI()
        prices = price_api.get_live_prices()
        return jsonify(prices)
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
        portfolio = CryptoPortfolioManager(initial_value_per_crypto=100.0)
        
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