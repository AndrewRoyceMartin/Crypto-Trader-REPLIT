#!/usr/bin/env python3
"""
Main Flask application entry point for deployment.
This file ensures proper deployment configuration and serves as the primary entry point.
"""

import os
from web_interface import app, initialize_system

def main():
    """Main entry point for the Flask application."""
    # Initialize the trading system
    initialize_system()
    
    # Get port from environment (required for Replit deployment)
    port = int(os.environ.get("PORT", "5000"))
    
    # Run the Flask application
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()