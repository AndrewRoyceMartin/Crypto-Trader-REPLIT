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

# --- Fast-boot knobs ---
WATCHLIST = [s.strip() for s in os.getenv(
    "WATCHLIST",
    "BTC,ETH,SOL,XRP,DOGE,BNB,ADA,AVAX,LINK,UNI"
).split(",") if s.strip()]

MAX_STARTUP_SYMBOLS   = int(os.getenv("MAX_STARTUP_SYMBOLS", "10"))   # how many to prefetch at boot
STARTUP_OHLCV_LIMIT   = int(os.getenv("STARTUP_OHLCV_LIMIT", "300"))  # bars per symbol at boot
WARMUP_CHUNK_SIZE     = int(os.getenv("WARMUP_CHUNK_SIZE", "3"))      # fetch N symbols in a batch
WARMUP_SLEEP_SEC      = int(os.getenv("WARMUP_SLEEP_SEC", "1"))       # pause between batches (rate-limit)
STARTUP_TIMEOUT_SEC   = int(os.getenv("STARTUP_TIMEOUT_SEC", "15"))   # soft budget; we never block beyond this

# Warm-up state & simple in-memory cache
warmup = {"started": False, "done": False, "error": "", "loaded": [], "start_time": None}
price_cache = {}  # key: (symbol,timeframe) -> DataFrame
cache_lock = threading.RLock()

def initialize_lightweight():
    """Initialize only essential components needed for Flask to start."""
    try:
        # Import here to avoid circular imports
        from src.utils.database import DatabaseManager
        from src.utils.logging import setup_logging
        
        # Setup basic logging
        setup_logging()
        logger.info("Lightweight initialization started")
        
        # Initialize database
        db = DatabaseManager()
        logger.info("Database initialized successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Lightweight initialization failed: {e}")
        return False

def background_warmup():
    """Initialize trading system components in background."""
    global warmup, app
    
    try:
        warmup["started"] = True
        warmup["start_time"] = datetime.now()
        logger.info("Background warmup started")
        
        # Import trading system components
        from web_interface import initialize_system, app as main_app
        
        # Initialize the full trading system
        initialize_system()
        
        # Register routes from main app (but only after warmup)
        logger.info("Registering main application routes")
        with app.app_context():
            # Copy all routes except ones we already have
            for rule in main_app.url_map.iter_rules():
                endpoint = rule.endpoint
                if endpoint not in ['health', 'ready', 'warmup_status', 'index'] and endpoint not in app.view_functions:
                    try:
                        # Create a new route in our app that calls the main app's view function
                        view_func = main_app.view_functions[endpoint]
                        app.add_url_rule(rule.rule, endpoint, view_func, methods=list(rule.methods))
                    except Exception as route_error:
                        logger.warning(f"Could not register route {rule.rule}: {route_error}")
        
        warmup["done"] = True
        warmup["loaded"] = WATCHLIST[:MAX_STARTUP_SYMBOLS]
        logger.info("Background warmup completed successfully")
        
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
    """Main dashboard route - will redirect to main app after warmup."""
    if warmup["done"]:
        # Redirect to the main web interface that's now loaded
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading System - Ready</title>
            <meta http-equiv="refresh" content="1;url=/dashboard">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .ready {{ color: green; animation: pulse 1s ease-in-out infinite; }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
            </style>
        </head>
        <body>
            <h1 class="ready">✅ Trading System Ready!</h1>
            <p>Currency selector and all trading features are now available.</p>
            <p>Redirecting to main dashboard...</p>
            <p><a href="/dashboard">Click here if not redirected automatically</a></p>
        </body>
        </html>
        """
    else:
        # Show loading page
        elapsed = ""
        if warmup["start_time"]:
            elapsed_sec = (datetime.now() - warmup["start_time"]).total_seconds()
            elapsed = f" ({elapsed_sec:.1f}s)"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading System - Loading</title>
            <meta http-equiv="refresh" content="3">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .loading {{ animation: spin 1s linear infinite; display: inline-block; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                .progress {{ width: 80%; background: #f0f0f0; margin: 20px auto; height: 10px; border-radius: 5px; }}
                .progress-bar {{ height: 100%; background: linear-gradient(90deg, #007bff, #28a745); border-radius: 5px; animation: progress 30s linear; }}
                @keyframes progress {{ 0% {{ width: 0%; }} 100% {{ width: 100%; }} }}
            </style>
        </head>
        <body>
            <h1>🚀 Trading System Loading{elapsed}</h1>
            <div class="loading">⚡</div>
            <div class="progress"><div class="progress-bar"></div></div>
            <p>Initializing currency selector and live price feeds...</p>
            <p>Status: {"Starting up..." if not warmup["started"] else "Loading live cryptocurrency data..."}</p>
            <p><small>Auto-refreshing every 3 seconds...</small></p>
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