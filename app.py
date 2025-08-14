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
    """Render the complete trading dashboard when system is ready."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crypto Trading System - Live Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            .currency-selector {{ font-size: 0.9rem; min-width: 120px; }}
            .price-display {{ font-family: 'Courier New', monospace; font-weight: bold; }}
            .status-connected {{ color: #28a745; }}
            .status-error {{ color: #dc3545; }}
            .portfolio-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
            .trading-card {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }}
        </style>
    </head>
    <body class="bg-light">
        <!-- Header with currency selector -->
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <span class="navbar-brand">
                    <i class="fas fa-chart-line me-2"></i>Crypto Trading System
                </span>
                <div class="d-flex align-items-center">
                    <label class="text-white me-2">Currency:</label>
                    <select class="form-select currency-selector me-3" id="currencySelector">
                        <option value="BTC/USDT">Bitcoin (BTC)</option>
                        <option value="ETH/USDT">Ethereum (ETH)</option>
                        <option value="SOL/USDT">Solana (SOL)</option>
                        <option value="XRP/USDT">Ripple (XRP)</option>
                        <option value="DOGE/USDT">Dogecoin (DOGE)</option>
                    </select>
                    <span class="badge bg-success" id="connectionStatus">
                        <i class="fas fa-circle me-1"></i>Live
                    </span>
                </div>
            </div>
        </nav>

        <!-- Main Dashboard -->
        <div class="container-fluid py-4">
            <div class="row">
                <!-- Portfolio Overview -->
                <div class="col-md-8">
                    <div class="card portfolio-card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-wallet me-2"></i>Portfolio Overview
                            </h5>
                            <div class="row">
                                <div class="col-md-3">
                                    <h6>Total Value</h6>
                                    <div class="price-display h4" id="totalValue">$12,450.67</div>
                                </div>
                                <div class="col-md-3">
                                    <h6>24h Change</h6>
                                    <div class="price-display h5" id="dayChange">+$234.50 (1.92%)</div>
                                </div>
                                <div class="col-md-3">
                                    <h6>Current Price</h6>
                                    <div class="price-display h5" id="currentPrice">Loading...</div>
                                </div>
                                <div class="col-md-3">
                                    <h6>Last Updated</h6>
                                    <div class="price-display" id="lastUpdate">Just now</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Price Chart -->
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-chart-area me-2"></i>Price Chart
                            </h5>
                            <canvas id="priceChart" height="100"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Trading Controls -->
                <div class="col-md-4">
                    <div class="card trading-card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-exchange-alt me-2"></i>Quick Trade
                            </h5>
                            <div class="mb-3">
                                <label class="form-label">Amount</label>
                                <input type="number" class="form-control" id="tradeAmount" placeholder="0.00">
                            </div>
                            <div class="d-grid gap-2">
                                <button class="btn btn-success" id="buyBtn" disabled>
                                    <i class="fas fa-arrow-up me-2"></i>Buy
                                </button>
                                <button class="btn btn-danger" id="sellBtn" disabled>
                                    <i class="fas fa-arrow-down me-2"></i>Sell
                                </button>
                            </div>
                            <div class="mt-3 text-center">
                                <small>Trading disabled until live prices confirmed</small>
                            </div>
                        </div>
                    </div>

                    <!-- Holdings -->
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas fa-coins me-2"></i>Current Holdings
                            </h5>
                            <div id="holdingsList">
                                <div class="d-flex justify-content-between py-2">
                                    <span>BTC</span>
                                    <span class="price-display">0.02450 BTC</span>
                                </div>
                                <div class="d-flex justify-content-between py-2">
                                    <span>ETH</span>
                                    <span class="price-display">1.25680 ETH</span>
                                </div>
                                <div class="d-flex justify-content-between py-2">
                                    <span>SOL</span>
                                    <span class="price-display">15.00000 SOL</span>
                                </div>
                                <hr>
                                <div class="d-flex justify-content-between">
                                    <strong>Total USD:</strong>
                                    <strong class="price-display">$12,450.67</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Scripts -->
        <script>
            let priceChart;
            let currentSymbol = 'BTC/USDT';
            
            // Initialize chart
            function initChart() {{
                const ctx = document.getElementById('priceChart').getContext('2d');
                priceChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: [],
                        datasets: [{{
                            label: 'Price',
                            data: [],
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            tension: 0.4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        scales: {{
                            y: {{
                                beginAtZero: false,
                                ticks: {{
                                    callback: function(value) {{
                                        return '$' + value.toLocaleString();
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}

            // Load price data
            async function loadPriceData(symbol) {{
                try {{
                    const response = await fetch(`/api/price?symbol=${{symbol}}&limit=50`);
                    const data = await response.json();
                    
                    if (data.error) {{
                        throw new Error(data.error);
                    }}
                    
                    // Update chart
                    const labels = data.map(d => new Date(d.ts).toLocaleTimeString());
                    const prices = data.map(d => d.close);
                    
                    priceChart.data.labels = labels;
                    priceChart.data.datasets[0].data = prices;
                    priceChart.update();
                    
                    // Update current price
                    const currentPrice = prices[prices.length - 1];
                    document.getElementById('currentPrice').textContent = '$' + currentPrice.toLocaleString();
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                    
                    // Enable trading buttons when we have live prices
                    document.getElementById('buyBtn').disabled = false;
                    document.getElementById('sellBtn').disabled = false;
                    document.querySelector('.mt-3 small').textContent = 'Live prices active - Trading enabled';
                    
                }} catch (error) {{
                    console.error('Price loading error:', error);
                    document.getElementById('currentPrice').textContent = 'Price unavailable';
                    document.getElementById('connectionStatus').innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
                    document.getElementById('connectionStatus').className = 'badge bg-warning';
                }}
            }}

            // Currency selector change
            document.getElementById('currencySelector').addEventListener('change', function() {{
                currentSymbol = this.value;
                loadPriceData(currentSymbol);
            }});

            // Initialize dashboard
            document.addEventListener('DOMContentLoaded', function() {{
                initChart();
                loadPriceData(currentSymbol);
                
                // Refresh data every 30 seconds
                setInterval(() => loadPriceData(currentSymbol), 30000);
            }});
        </script>
    </body>
    </html>
    """

# Delegate all other routes to main app when ready
@app.route("/<path:path>", methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_to_main_app(path):
    """Proxy all routes to main app when ready."""
    if warmup["done"] and not warmup["error"]:
        try:
            from web_interface import app as main_app
            from flask import request
            
            # Forward the request to the main app
            with main_app.test_client() as client:
                response = client.open(
                    path=f'/{path}',
                    method=request.method,
                    headers=dict(request.headers),
                    data=request.get_data(),
                    query_string=request.query_string
                )
                
                # Return the response from main app
                from flask import Response
                return Response(
                    response.data,
                    status=response.status_code,
                    headers=dict(response.headers)
                )
                
        except Exception as e:
            logger.error(f"Proxy error for /{path}: {e}")
            return jsonify({"error": "Service temporarily unavailable"}), 503
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