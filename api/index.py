import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tell Django which settings to use and that we're on Vercel
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_django.settings')
os.environ['VERCEL'] = '1'

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
