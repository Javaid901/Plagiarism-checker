# Gunicorn config for Render (512MB RAM limit)
import os

# Bind to $PORT or 5000
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Single worker (more workers = more RAM)
workers = 1
threads = 4

# Timeout for long-running model inference
timeout = 120

# Reduce memory footprint
worker_class = "sync"
max_requests = 100
max_requests_jitter = 20

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "warning"

# Preload app to share memory across workers (only matters if workers > 1)
preload_app = True
