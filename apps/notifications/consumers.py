import json
from typing import Any, cast
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.blog.models import Post


User = get_user_model()


class CommentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # 1. Получаем slug
        url_route = self.scope.get("url_route")
        slug = ""
        if isinstance(url_route, dict):
            kwargs = url_route.get("kwargs")
            if isinstance(kwargs, dict):
                slug = str(kwargs.get("slug", ""))

        self.slug = slug
        self.group_name = f"post_comments_{self.slug}"

        # 2. Получаем token из query params
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if not token:
            await self.close(code=4001)
            return

        # 3. Валидируем токен
        try:
            access_token = AccessToken(cast(Any, token))
            user_id = access_token["user_id"]
        except Exception:
            await self.close(code=4001)
            return

        # 4. Получаем пользователя
        self.user = await self.get_user(user_id)
        if not self.user:
            await self.close(code=4001)
            return

        # 5. Проверяем пост
        self.post = await self.get_post(self.slug)
        if not self.post:
            await self.close(code=4004)
            return

        # 6. Подключаем к группе
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # 7. Принимаем соединение
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # 🔥 Это обработчик событий из group_send
    async def comment_created(self, event):
        await self.send(text_data=json.dumps({
            "comment_id": event["comment_id"],
            "author": event["author"],
            "body": event["body"],
            "created_at": event["created_at"],
        }))

    # --- DB helpers ---
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_post(self, slug):
        try:
            return Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            return None
