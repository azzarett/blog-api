from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.blog.models import Post

POSTS_LIST_CACHE_VERSION_KEY = 'posts:list:version'


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
