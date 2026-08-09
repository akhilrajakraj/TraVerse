from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)


def create_notification(
    *,
    user,
    notification_type: str,
    subject: str,
    body: str,
    channel: str = NotificationChannel.EMAIL,
) -> Notification:
    """
    Create a notification record synchronously and dispatch its
    delivery asynchronously.

    The database record is created first with PENDING status.
    Actual delivery is handled separately by Celery.
    """

    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        channel=channel,
        subject=subject,
        body=body,
        status=NotificationStatus.PENDING,
    )

    # Deferred import intentionally avoids import-order issues during
    # Django application loading.
    from apps.notifications.tasks import send_notification_task

    send_notification_task.delay(
        notification_id=str(notification.id),
    )

    return notification


def mark_as_read(*, notification: Notification) -> Notification:
    """
    Mark a notification as read.

    Read state is independent of delivery status.
    """

    notification.is_read = True

    notification.save(
        update_fields=[
            "is_read",
            "updated_at",
        ],
    )

    return notification