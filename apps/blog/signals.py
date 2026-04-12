import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from redis import Redis

from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.blog.models import Comment, Post

POSTS_LIST_CACHE_VERSION_KEY = 'posts:list:version'
COMMENTS_CHANNEL = 'comments:new'
POST_PUBLICATIONS_GROUP = 'post_publications'

logger = logging.getLogger(__name__)


def bump_posts_list_cache_version() -> None:
    try:
        cache.incr(POSTS_LIST_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(POSTS_LIST_CACHE_VERSION_KEY, 2, timeout=None)


def publish_post_published_event(post: Post) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    published_at = post.publish_at or timezone.now()
    payload = {
        'post_id': post.id,
        'title': post.title,
        'slug': post.slug,
        'author': {
            'id': post.author_id,
            'email': post.author.email,
        },
        'published_at': published_at.isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        POST_PUBLICATIONS_GROUP,
        {
            'type': 'post_published',
            'payload': payload,
        },
    )


@receiver(pre_save, sender=Post)
def store_previous_post_status(sender, instance: Post, **kwargs) -> None:
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        Post.objects.filter(pk=instance.pk)
        .values_list('status', flat=True)
        .first()
    )


@receiver(post_save, sender=Post)
def invalidate_posts_cache_on_save(sender, **kwargs) -> None:
    bump_posts_list_cache_version()


@receiver(post_save, sender=Post)
def publish_post_event_on_published(
    sender,
    instance: Post,
    created: bool,
    **kwargs,
) -> None:
    if instance.status != Post.Status.PUBLISHED:
        return

    previous_status = getattr(instance, '_previous_status', None)
    if not created and previous_status == Post.Status.PUBLISHED:
        return

    try:
        publish_post_published_event(instance)
    except Exception:
        logger.exception('Failed to publish post event to SSE group.')


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
