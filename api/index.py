import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set env vars BEFORE django loads settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_django.settings')
os.environ.setdefault('VERCEL', '1')

# Setup Django and run migrations on the fresh /tmp SQLite DB
import django
django.setup()

from django.core.management import call_command
try:
    call_command('migrate', '--run-syncdb', verbosity=0, interactive=False)
except Exception as e:
    print(f"[Startup] Migration skipped: {e}")

# Export the WSGI app (django.setup already called, get_wsgi_application is safe)
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
