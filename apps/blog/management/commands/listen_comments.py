import asyncio
import json

import redis.asyncio as redis

from django.conf import settings
from django.core.management.base import BaseCommand

CHANNEL_NAME = 'comments:new'


class Command(BaseCommand):
    help = 'Listen for comment events from Redis using an async pub/sub consumer.'

    def handle(self, *args, **options):
        try:
            asyncio.run(self._listen())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Stopped comment listener.'))

    async def _listen(self) -> None:
        # Async keeps a single event loop handling socket I/O efficiently; a
        # synchronous loop would block between reads and scale poorly.
        redis_client = redis.from_url(settings.BLOG_REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()

        await pubsub.subscribe(CHANNEL_NAME)
        self.stdout.write(self.style.SUCCESS(f'Listening on Redis channel: {CHANNEL_NAME}'))

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message is None:
                    await asyncio.sleep(0.1)
                    continue

                payload_raw = message.get('data')
                if not isinstance(payload_raw, str):
                    continue

                try:
                    payload = json.loads(payload_raw)
                except json.JSONDecodeError:
                    self.stdout.write(
                        self.style.WARNING('Received malformed JSON comment event.')
                    )
                    continue

                self.stdout.write(json.dumps(payload, ensure_ascii=False))
        finally:
            await pubsub.unsubscribe(CHANNEL_NAME)
            await pubsub.aclose()
            await redis_client.aclose()
