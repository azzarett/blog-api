from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
	comment_id = serializers.IntegerField(source='comment.id', read_only=True)

	class Meta:
		model = Notification
		fields = ('id', 'comment_id', 'is_read', 'created_at')


class NotificationUnreadCountSerializer(serializers.Serializer):
	unread_count = serializers.IntegerField()


class NotificationMarkReadSerializer(serializers.Serializer):
	marked_as_read = serializers.IntegerField()


class PaginatedNotificationListSerializer(serializers.Serializer):
	count = serializers.IntegerField()
	next = serializers.URLField(allow_null=True)
	previous = serializers.URLField(allow_null=True)
	results = NotificationSerializer(many=True)
