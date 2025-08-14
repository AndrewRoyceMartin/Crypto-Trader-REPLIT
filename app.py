#!/usr/bin/env python3
"""
Main Flask application entry point for deployment.
This file ensures proper deployment configuration and serves as the primary entry point.
"""

import os
import sys
import logging
from web_interface import app, initialize_system

# Set up logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Flask application."""
    try:
        logger.info("Starting Flask application for deployment...")
        
        # Initialize the trading system
        initialize_system()
        logger.info("Trading system initialized successfully")
        
        # Get port from environment (required for Replit deployment)
        port = int(os.environ.get("PORT", "5000"))
        logger.info(f"Starting Flask app on host 0.0.0.0, port {port}")
        
        # Run the Flask application
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=False, 
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        sys.exit(1)

# Ensure this can be imported for WSGI as well
application = app

if __name__ == "__main__":
    main()