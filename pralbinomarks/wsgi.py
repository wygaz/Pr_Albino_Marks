import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pralbinomarks.settings')

try:
    application = get_wsgi_application()
except Exception as e:
    import traceback
    traceback.print_exc()
