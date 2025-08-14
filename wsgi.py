"""
WSGI configuration for production deployment.
This file is required for proper deployment on Replit Autoscale.
"""

from web_interface import app, initialize_system

# Initialize the system when the module is imported
initialize_system()

# This is the WSGI application that will be called by the server
application = app

if __name__ == "__main__":
    # For local development
    import os
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)