from celery import shared_task
from django.contrib.auth import get_user_model
from apps.blog.models import Comment, Post
from apps.notifications.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def process_new_comment(comment_id):
    # Retry is critical here to avoid losing notifications and real-time events.
    comment = Comment.objects.select_related("author", "post").get(id=comment_id)
    post = comment.post

    # 1. Создать notification
    if comment.author != post.author:
        Notification.objects.create(
            recipient=post.author,
            comment=comment
        )

    # 2. Отправить в WebSocket
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"post_comments_{post.slug}",
        {
            "type": "comment_created",
            "comment_id": comment.id,
            "author": {
                "id": comment.author.id,
                "email": comment.author.email,
            },
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
        }
    )