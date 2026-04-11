from django.urls import path

from apps.notifications.views import (
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationUnreadCountAPIView,
)

urlpatterns = [
    path('api/notifications/count/', NotificationUnreadCountAPIView.as_view()),
    path('api/notifications/', NotificationListAPIView.as_view()),
    path('api/notifications/read/', NotificationMarkReadAPIView.as_view()),
]
