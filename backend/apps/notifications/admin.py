"""
Django admin configuration for the Notifications application.
"""

from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification records.
    """

    list_display = (
        "user",
        "notification_type",
        "channel",
        "status",
        "is_read",
        "sent_at",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "channel",
        "status",
        "is_read",
    )

    search_fields = (
        "user__email",
        "subject",
        "body",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "sent_at",
    )

    list_select_related = (
        "user",
    )

    ordering = (
        "-created_at",
    )