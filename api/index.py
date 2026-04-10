import os
import sys
from django.core.wsgi import get_wsgi_application

# Robust path handling
path = os.path.dirname(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_django.settings')

app = get_wsgi_application()
