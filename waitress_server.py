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
        threads=2
    )