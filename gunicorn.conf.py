# gunicorn.conf.py
import multiprocessing

# Use only 1 worker for free tier (256MB RAM)
workers = 1
worker_class = "sync"

# Bind to Render's port
bind = "0.0.0.0:10000"

# Timeouts (shorter for free tier)
timeout = 30
keepalive = 2

# Limit connections
worker_connections = 100

# Disable preload to save memory
preload_app = False

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "warning"

# Process naming
proc_name = "edaptiv"