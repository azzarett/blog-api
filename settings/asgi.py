import os

from django.core.asgi import get_asgi_application

# ❗ ЖЁСТКО задаём settings (не setdefault)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.env.prod'

# ❗ сначала инициализация Django
django_asgi_app = get_asgi_application()

# ❗ только ПОСЛЕ этого импортируем Channels stuff
from channels.routing import ProtocolTypeRouter, URLRouter
import apps.notifications.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(
        apps.notifications.routing.websocket_urlpatterns
    ),
})