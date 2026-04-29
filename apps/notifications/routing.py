from typing import Any, cast

from django.urls import path
from .consumers import CommentConsumer

websocket_urlpatterns = [
    path("ws/posts/<slug:slug>/comments/", cast(Any, CommentConsumer.as_asgi())),
]
