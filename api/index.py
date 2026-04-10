import os
import sys
import traceback

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manager_django.settings')

try:
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
except Exception as e:
    print("Error initializing Django application:")
    traceback.print_exc()
    raise e
