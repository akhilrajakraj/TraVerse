from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.models import Notification


def send_email_notification(notification: Notification) -> None:
    """
    Deliver a notification through Django's configured email backend.

    The notification task is responsible for delivery lifecycle state;
    this backend is responsible only for performing the actual email
    delivery.
    """

    send_mail(
        subject=notification.subject,
        message=notification.body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[notification.user.email],
        fail_silently=False,
    )