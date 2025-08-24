"""
WSGI configuration for production deployment.
This file is required for proper deployment on Replit Autoscale.
"""

import os
from app import app, initialize_system

# Initialize the trading system on module import
initialize_system()

# Configure Flask for deployment
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# This is the WSGI application that will be called by the server
application = app

if __name__ == "__main__":
    # For local development
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)