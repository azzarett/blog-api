import os

from django.core.wsgi import get_wsgi_application

DJANGO_SETTINGS_MODULE_KEY = 'DJANGO_SETTINGS_MODULE'
DEFAULT_SETTINGS_MODULE = 'settings.env.local'

os.environ.setdefault(DJANGO_SETTINGS_MODULE_KEY, DEFAULT_SETTINGS_MODULE)

application = get_wsgi_application()
