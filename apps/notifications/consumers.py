import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CommentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        url_route = self.scope.get("url_route")
        slug = ""
        if isinstance(url_route, dict):
            kwargs = url_route.get("kwargs")
            if isinstance(kwargs, dict):
                slug = str(kwargs.get("slug", ""))

        self.slug = slug
        self.group_name = f"comments_{self.slug}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return

        data = json.loads(text_data)
        message = data.get("message")

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "comment_message",
                "message": message,
            }
        )

    async def comment_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({
            "message": message
        }))
