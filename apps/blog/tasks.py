from celery import shared_task

from django.core.cache import cache

POSTS_LIST_CACHE_VERSION_KEY = 'posts:list:version'

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def invalidate_posts_cache():
    # Retry protects against transient Redis/cache connectivity issues.
    try:
        cache.incr(POSTS_LIST_CACHE_VERSION_KEY)
    except ValueError:
        cache.set(POSTS_LIST_CACHE_VERSION_KEY, 2, timeout=None)