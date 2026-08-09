"""
Backend tests for the Notifications application.
"""

from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.backends import send_email_notification
from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


User = get_user_model()


class NotificationEmailBackendTests(TestCase):
    """
    Test suite for the notification email backend.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

        self.notification = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            channel=NotificationChannel.EMAIL,
            subject="Trip plan ready",
            body="Your trip plan is ready.",
            status=NotificationStatus.PENDING,
        )

    @patch("apps.notifications.backends.send_mail")
    def test_send_email_notification(self, mock_send_mail):
        """
        Backend should send the notification using Django's
        configured email backend.
        """

        send_email_notification(
            notification=self.notification,
        )

        mock_send_mail.assert_called_once_with(
            subject="Trip plan ready",
            message="Your trip plan is ready.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["user@example.com"],
            fail_silently=False,
        )

    @patch("apps.notifications.backends.send_mail")
    def test_send_email_notification_uses_notification_recipient(
        self,
        mock_send_mail,
    ):
        """
        Backend should send the email to the notification owner's
        email address.
        """

        self.user.email = "recipient@example.com"
        self.user.save(update_fields=["email"])

        self.notification.refresh_from_db()

        send_email_notification(
            notification=self.notification,
        )

        mock_send_mail.assert_called_once_with(
            subject=self.notification.subject,
            message=self.notification.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["recipient@example.com"],
            fail_silently=False,
        )

    @patch("apps.notifications.backends.send_mail")
    def test_send_email_notification_does_not_update_notification_state(
        self,
        mock_send_mail,
    ):
        """
        The backend should only perform email delivery.

        Delivery lifecycle state is owned by the Celery task, not
        the email backend.
        """

        send_email_notification(
            notification=self.notification,
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification.status,
            NotificationStatus.PENDING,
        )

        self.assertIsNone(
            self.notification.sent_at,
        )

        self.assertEqual(
            self.notification.error_message,
            "",
        )

        mock_send_mail.assert_called_once()

    @patch(
        "apps.notifications.backends.send_mail",
        side_effect=RuntimeError("SMTP server unavailable"),
    )
    def test_send_email_notification_propagates_delivery_error(
        self,
        mock_send_mail,
    ):
        """
        Backend should propagate email delivery errors so the Celery
        task can handle retries and failure state.
        """

        with self.assertRaises(RuntimeError) as context:
            send_email_notification(
                notification=self.notification,
            )

        self.assertEqual(
            str(context.exception),
            "SMTP server unavailable",
        )

        mock_send_mail.assert_called_once()