from celery import shared_task
from django.utils import timezone

from apps.notifications.backends import send_email_notification
from apps.notifications.models import Notification, NotificationStatus


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_notification_task(self, notification_id: str) -> None:
    notification = Notification.objects.get(
        pk=notification_id,
    )

    try:
        if notification.status == NotificationStatus.SENT:
            return

        send_email_notification(notification)

        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.error_message = ""

        notification.save(
            update_fields=[
                "status",
                "sent_at",
                "error_message",
                "updated_at",
            ],
        )

    except Exception as exc:
        notification.status = NotificationStatus.FAILED
        notification.error_message = str(exc)

        notification.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ],
        )

        raise