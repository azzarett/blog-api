import json
import logging

from redis import Redis

from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.blog.models import Comment, Post

POSTS_LIST_CACHE_VERSION_KEY = 'posts:list:version'
COMMENTS_CHANNEL = 'comments:new'

logger = logging.getLogger(__name__)


def bump_posts_list_cache_version() -> None:
    try:
        cache.incr(POSTS_LIST_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(POSTS_LIST_CACHE_VERSION_KEY, 2, timeout=None)


@receiver(post_save, sender=Post)
def invalidate_posts_cache_on_save(sender, **kwargs) -> None:
    bump_posts_list_cache_version()


@receiver(post_delete, sender=Post)
def invalidate_posts_cache_on_delete(sender, **kwargs) -> None:
    bump_posts_list_cache_version()


@receiver(post_save, sender=Comment)
def publish_comment_event_on_create(sender, instance: Comment, created: bool, **kwargs) -> None:
    if not created:
        return

    payload = {
        'post_slug': instance.post.slug,
        'author_id': instance.author_id,
        'comment_body': instance.body,
    }

    try:
        redis_client = Redis.from_url(settings.BLOG_REDIS_URL, decode_responses=True)
        redis_client.publish(COMMENTS_CHANNEL, json.dumps(payload, ensure_ascii=False))
        redis_client.close()
    except Exception:
        logger.exception('Failed to publish comment event to Redis.')
