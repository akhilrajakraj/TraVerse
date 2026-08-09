"""
Serializers for the Notifications application.
"""

from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Read serializer for notifications.

    Notification content and delivery state are controlled by the
    notification system. The authenticated user may only change
    whether the notification has been read.
    """

    class Meta:
        model = Notification

        fields = [
            "id",
            "notification_type",
            "subject",
            "body",
            "status",
            "is_read",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "notification_type",
            "subject",
            "body",
            "status",
            "created_at",
        ]