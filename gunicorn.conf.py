# Gunicorn configuration for production deployment
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = 2
worker_class = "gthread"
threads = 8
worker_connections = 1000
timeout = 60
keepalive = 30

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "trading_system"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None
preload_app = True

# SSL
keyfile = None
certfile = None
