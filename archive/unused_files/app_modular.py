#!/usr/bin/env python3
"""
Modular Flask application entry point.
Demonstrates the new modular architecture with api/, portfolio/, and trading/ modules.
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime, timezone
from flask import Flask, jsonify

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Global state for the modular app
server_start_time = datetime.now(timezone.utc)

def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # Register blueprints
    try:
        from api.routes import api_bp
        app.register_blueprint(api_bp)
        logger.info("Registered API blueprint")
    except ImportError as e:
        logger.warning(f"Could not import API blueprint: {e}")
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy", 
            "uptime": int((datetime.now(timezone.utc) - server_start_time).total_seconds())
        })
    
    # Root endpoint
    @app.route('/')
    def index():
        from flask import render_template
        try:
            return render_template('unified_dashboard.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return jsonify({"message": "Trading Dashboard", "status": "running"})
    
    return app

def initialize_system() -> bool:
    """Initialize system components."""
    try:
        # Initialize database
        from src.utils.database import DatabaseManager
        _ = DatabaseManager()
        logger.info("Database initialized")
        
        # Initialize portfolio service
        from src.services.portfolio_service import get_portfolio_service
        portfolio_service = get_portfolio_service()
        if portfolio_service:
            logger.info("Portfolio service initialized")
        
        return True
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return False

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    logger.info("Starting modular trading application...")
    
    # Initialize system
    if initialize_system():
        logger.info("System initialization completed")
    else:
        logger.error("System initialization failed")
        sys.exit(1)
    
    # Start the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)