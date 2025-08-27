"""
API Routes Module
Handles all Flask routes and API endpoints
"""
from flask import Blueprint, request, jsonify, render_template, Response
from typing import Any, Dict
import logging
import time
from datetime import datetime

# Create API blueprint
api_bp = Blueprint('api', __name__)

logger = logging.getLogger(__name__)

# Import shared utilities and services
try:
    from portfolio.manager import get_portfolio_summary
    from trading.bot import get_bot_status, get_bot_state
except ImportError:
    # Fallback for development
    pass

@api_bp.route("/api/status")
def api_status():
    """Get system status and portfolio summary."""
    try:
        from .core import get_uptime_seconds, iso_utc
        from portfolio.manager import get_portfolio_summary
        from trading.bot import get_bot_status
        
        portfolio_summary = get_portfolio_summary()
        bot_status = get_bot_status()
        
        return jsonify({
            "status": "connected",
            "timestamp": time.time(),
            "portfolio": portfolio_summary,
            "bot": bot_status,
            "uptime_seconds": get_uptime_seconds()
        })
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({"error": "Service unavailable"}), 500

@api_bp.route("/health")
def health_check():
    """Basic health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": time.time()})

@api_bp.route("/ready")
def readiness_check():
    """Readiness check for deployment."""
    try:
        # Add basic system checks here
        return jsonify({"status": "ready", "timestamp": time.time()})
    except Exception:
        return jsonify({"status": "not ready"}), 503