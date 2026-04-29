from django.db import models

from apps.blog.models import Comment

RECIPIENT_RELATED_NAME = 'notifications'
COMMENT_RELATED_NAME = 'notifications'


class Notification(models.Model):
	recipient = models.ForeignKey(
		'users.User',
		on_delete=models.CASCADE,
		related_name=RECIPIENT_RELATED_NAME,
	)
	comment = models.ForeignKey(
		Comment,
		on_delete=models.CASCADE,
		related_name=COMMENT_RELATED_NAME,
	)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		indexes = [
			models.Index(fields=['recipient', 'is_read']),
		]
		ordering = ['-created_at']

