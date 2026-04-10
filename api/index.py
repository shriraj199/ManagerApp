import os
import sys

# Robust path handling — add project root to Python path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_django.settings')
os.environ.setdefault('VERCEL', '1')

# Run migrations on /tmp db (ephemeral but needed for Django to start)
from django.core.management import call_command
import django
django.setup()
try:
    call_command('migrate', '--run-syncdb', verbosity=0, interactive=False)
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
