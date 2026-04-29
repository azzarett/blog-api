import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

import apps.notifications.routing

DJANGO_SETTINGS_MODULE_KEY = 'DJANGO_SETTINGS_MODULE'
DEFAULT_SETTINGS_MODULE = 'settings.env.local'

os.environ.setdefault(DJANGO_SETTINGS_MODULE_KEY, DEFAULT_SETTINGS_MODULE)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": URLRouter(
        apps.notifications.routing.websocket_urlpatterns
    ),
})
