#!/usr/bin/env python3
"""
Main Flask application entry point for deployment.
Fast-boot approach: start Flask immediately, initialize trading system in background.
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from flask import Flask, jsonify

# Set up logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# --- Fast-boot knobs (extra hardening) ---
WATCHLIST = [s.strip() for s in os.getenv(
    "WATCHLIST",
    "BTC,ETH,SOL,XRP,DOGE,BNB,ADA,AVAX,LINK,UNI"
).split(",") if s.strip()]

MAX_STARTUP_SYMBOLS   = int(os.getenv("MAX_STARTUP_SYMBOLS", "5"))     # reduced: only 5 symbols at boot
STARTUP_OHLCV_LIMIT   = int(os.getenv("STARTUP_OHLCV_LIMIT", "150"))  # reduced: 150 bars per symbol
WARMUP_CHUNK_SIZE     = int(os.getenv("WARMUP_CHUNK_SIZE", "2"))      # smaller chunks: 2 symbols at a time
WARMUP_SLEEP_SEC      = int(os.getenv("WARMUP_SLEEP_SEC", "1"))       # base pause between batches
STARTUP_TIMEOUT_SEC   = int(os.getenv("STARTUP_TIMEOUT_SEC", "8"))    # reduced: 8 second budget
CACHE_FILE            = "warmup_cache.parquet"                        # persistent cache file

# Warm-up state & simple in-memory cache
warmup = {"started": False, "done": False, "error": "", "loaded": [], "start_time": None}
price_cache = {}  # key: (symbol,timeframe) -> DataFrame
cache_lock = threading.RLock()

def cache_put(symbol: str, timeframe: str, df):
    """Store DataFrame in cache and optionally persist to disk."""
    with cache_lock:
        price_cache[(symbol, timeframe)] = df

def cache_get(symbol: str, timeframe: str):
    """Retrieve DataFrame from cache."""
    with cache_lock:
        return price_cache.get((symbol, timeframe))

def load_persistent_cache():
    """Load yesterday's OHLCV data from disk cache for instant boot."""
    try:
        if os.path.exists(CACHE_FILE):
            import pandas as pd
            logger.info(f"Loading persistent cache from {CACHE_FILE}")
            cached_data = pd.read_parquet(CACHE_FILE)
            
            # Parse cached data back into price_cache format
            for symbol in cached_data['symbol'].unique():
                symbol_data = cached_data[cached_data['symbol'] == symbol].copy()
                symbol_data = symbol_data.drop('symbol', axis=1)
                symbol_data.set_index('timestamp', inplace=True)
                cache_put(symbol, '1d', symbol_data)
            
            logger.info(f"Loaded {len(cached_data['symbol'].unique())} symbols from persistent cache")
            return True
    except Exception as e:
        logger.warning(f"Could not load persistent cache: {e}")
    return False

def save_persistent_cache():
    """Save current cache to disk for next boot."""
    try:
        import pandas as pd
        all_data = []
        
        with cache_lock:
            for (symbol, timeframe), df in price_cache.items():
                if timeframe == '1d' and not df.empty:
                    df_copy = df.copy().reset_index()
                    df_copy['symbol'] = symbol
                    all_data.append(df_copy)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df.to_parquet(CACHE_FILE, index=False)
            logger.info(f"Saved {len(all_data)} symbol datasets to persistent cache")
    except Exception as e:
        logger.warning(f"Could not save persistent cache: {e}")

def get_df(symbol: str, timeframe: str):
    """Get OHLCV data with fallback fetch."""
    df = cache_get(symbol, timeframe)
    if df is not None:
        return df
    
    # Fallback: fetch just-in-time for requested symbol only
    try:
        from src.config import Config
        from src.adapters.okx_adapter import OKXAdapter
        
        ex = OKXAdapter(Config()).exchange
        ex.load_markets()
        
        # Exponential backoff for API calls
        import time
        for attempt in range(3):
            try:
                ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=STARTUP_OHLCV_LIMIT)
                break
            except Exception as api_error:
                if attempt < 2:
                    wait_time = (2 ** attempt) * WARMUP_SLEEP_SEC
                    logger.warning(f"API error for {symbol}, retrying in {wait_time}s: {api_error}")
                    time.sleep(wait_time)
                else:
                    raise api_error
        
        import pandas as pd
        df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df.set_index("ts", inplace=True)
        cache_put(symbol, timeframe, df)
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol}: {e}")
        import pandas as pd
        return pd.DataFrame()  # Return empty DataFrame on failure

def initialize_lightweight():
    """Initialize only essential components needed for Flask to start."""
    try:
        # Import here to avoid circular imports
        from src.utils.database import DatabaseManager
        from src.utils.logging import setup_logging
        
        # Setup basic logging
        setup_logging()
        logger.info("Lightweight initialization started")
        
        # Try to load persistent cache first for instant data availability
        cache_loaded = load_persistent_cache()
        if cache_loaded:
            logger.info("Instant cache loaded - some data available immediately")
        
        # Initialize database
        db = DatabaseManager()
        logger.info("Database initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Lightweight initialization failed: {e}")
        return False

def background_warmup():
    """Initialize trading system components in background with timeout."""
    global warmup, app
    
    try:
        warmup["started"] = True
        start_time = datetime.now()
        warmup["start_time"] = start_time
        logger.info(f"Background warmup started with {STARTUP_TIMEOUT_SEC}s timeout")
        
        # Quick timeout check function
        def check_timeout():
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > STARTUP_TIMEOUT_SEC:
                logger.warning(f"Warmup timeout reached ({elapsed:.1f}s > {STARTUP_TIMEOUT_SEC}s)")
                return True
            return False
        
        # Import trading system components (with timeout check)
        if check_timeout():
            raise TimeoutError("Timeout during import phase")
            
        from web_interface import initialize_system, app as main_app
        
        # Initialize only essential components quickly
        if check_timeout():
            raise TimeoutError("Timeout before initialization")
            
        initialize_system()
        
        # Save current cache state for next boot
        save_persistent_cache()
        
        # Don't register routes during app runtime - causes Flask errors
        # Routes will be available when user navigates to main app endpoints
        
        warmup["done"] = True
        warmup["loaded"] = WATCHLIST[:MAX_STARTUP_SYMBOLS]
        logger.info(f"Background warmup completed in {(datetime.now() - start_time).total_seconds():.1f}s")
        
    except TimeoutError as e:
        logger.warning(f"Background warmup timeout: {e}")
        warmup["error"] = f"Timeout after {STARTUP_TIMEOUT_SEC}s"
        warmup["done"] = True
    except Exception as e:
        error_msg = f"Background warmup failed: {str(e)}"
        logger.error(error_msg)
        warmup["error"] = error_msg
        warmup["done"] = True  # Mark as done even if failed

# Create Flask app instance
app = Flask(__name__)

# Add fast-boot health endpoints to the Flask app
@app.route("/health")
def health():
    """For the platform restart logic: 200 as soon as we're listening."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200

@app.route("/ready")
def ready():
    """For your UI: only 200 when warm-up has finished."""
    if warmup["done"]:
        return jsonify({"ready": True, **warmup}), 200
    else:
        return jsonify({"ready": False, **warmup}), 503

@app.route("/api/warmup")
def warmup_status():
    """Get detailed warmup status."""
    status = dict(warmup)
    if warmup["start_time"]:
        elapsed = (datetime.now() - warmup["start_time"]).total_seconds()
        status["elapsed_seconds"] = round(elapsed, 2)
    return jsonify(status), 200

@app.route("/")
def index():
    """Main dashboard route with circuit breaker pattern."""
    if warmup["done"] and not warmup["error"]:
        # System ready - redirect to main interface
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading System - Ready</title>
            <meta http-equiv="refresh" content="0;url=/dashboard">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .ready {{ color: green; }}
            </style>
        </head>
        <body>
            <h1 class="ready">✅ Trading System Ready!</h1>
            <p>Redirecting to dashboard with currency selector...</p>
            <p><a href="/dashboard">Click here if not redirected</a></p>
        </body>
        </html>
        """
    elif warmup["done"] and warmup["error"]:
        # System failed to initialize properly
        return render_loading_skeleton(f"System Error: {warmup['error']}", error=True)
    else:
        # Show loading skeleton while warming up
        return render_loading_skeleton()

# Fallback route handler that delegates to main app when ready
@app.route("/<path:path>")
def catch_all(path):
    """Catch-all route that delegates to main app when ready."""
    if warmup["done"] and not warmup["error"]:
        try:
            from web_interface import app as main_app
            with main_app.test_request_context(f'/{path}'):
                try:
                    return main_app.full_dispatch_request()
                except Exception:
                    # If route doesn't exist in main app, return 404
                    from flask import abort
                    abort(404)
        except Exception as e:
            logger.error(f"Error serving path /{path}: {e}")
            return render_loading_skeleton("Error loading page")
    else:
        return render_loading_skeleton("System still initializing...")

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
    # Fast initialization - only what's needed for Flask to start
    if not initialize_lightweight():
        logger.error("Failed lightweight initialization")
        sys.exit(1)
    
    # Start background warmup immediately
    warmup_thread = threading.Thread(target=background_warmup, daemon=True)
    warmup_thread.start()
    
    # Start Flask server immediately
    port = int(os.environ.get("PORT", "5000"))  # Replit/host injects PORT
    logger.info(f"Starting Flask server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)