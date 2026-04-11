from drf_spectacular.utils import extend_schema

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification
from apps.notifications.serializers import (
	NotificationMarkReadSerializer,
	NotificationSerializer,
	NotificationUnreadCountSerializer,
	PaginatedNotificationListSerializer,
)


class NotificationUnreadCountAPIView(APIView):
	permission_classes = (IsAuthenticated,)

	@extend_schema(responses={200: NotificationUnreadCountSerializer})
	def get(self, request, *args, **kwargs) -> Response:
		unread_count = Notification.objects.filter(
			recipient=request.user,
			is_read=False,
		).count()
		return Response({'unread_count': unread_count})


class NotificationListAPIView(generics.ListAPIView):
	permission_classes = (IsAuthenticated,)
	serializer_class = NotificationSerializer

	# Polling is easy to adopt and works with plain HTTP clients, but it adds
	# delay and repeated requests; move to SSE/WebSocket for high-frequency UX.
	@extend_schema(responses={200: PaginatedNotificationListSerializer})
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)

	def get_queryset(self):
		return Notification.objects.filter(recipient=self.request.user).select_related(
			'comment'
		)


class NotificationMarkReadAPIView(APIView):
	permission_classes = (IsAuthenticated,)

	@extend_schema(responses={200: NotificationMarkReadSerializer})
	def post(self, request, *args, **kwargs) -> Response:
		updated_count = Notification.objects.filter(
			recipient=request.user,
			is_read=False,
		).update(is_read=True)
		return Response({'marked_as_read': updated_count})
