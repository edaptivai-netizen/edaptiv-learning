# waitress_server.py
import os
from waitress import serve
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

if __name__ == "__main__":
    # Render uses port 10000
    print("🚀 Starting Waitress server on port 10000...")
    serve(
        application, 
        host="0.0.0.0", 
        port=10000, 
        threads=4,           # More threads for health checks
        connection_limit=100, # Limit connections
        asyncore_loop_timeout=1,  # Faster loop
        channel_timeout=10,  # Shorter timeout
        cleanup_interval=30  # Clean up old connections
    )