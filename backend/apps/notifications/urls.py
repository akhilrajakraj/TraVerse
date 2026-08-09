from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    NotificationMarkReadView,
)

app_name = "notifications"

urlpatterns = [
    path(
        "",
        NotificationListView.as_view(),
        name="notification-list",
    ),
    path(
        "<uuid:notification_pk>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-mark-read",
    ),
]