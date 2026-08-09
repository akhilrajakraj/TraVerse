"""
Celery task tests for the Notifications application.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.tasks import send_notification_task


User = get_user_model()


class NotificationTaskTests(TestCase):
    """
    Test suite for asynchronous notification delivery.
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

    @patch("apps.notifications.tasks.send_email_notification")
    def test_send_notification_marks_notification_as_sent(
        self,
        mock_send_email,
    ):
        """
        Successful email delivery should transition the notification
        from PENDING to SENT.
        """

        send_notification_task.run(
            notification_id=str(self.notification.id),
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification.status,
            NotificationStatus.SENT,
        )

        self.assertIsNotNone(
            self.notification.sent_at,
        )

        self.assertEqual(
            self.notification.error_message,
            "",
        )

        mock_send_email.assert_called_once_with(
            self.notification,
        )

    @patch(
        "apps.notifications.tasks.send_email_notification",
        side_effect=RuntimeError("Email delivery failed."),
    )
    def test_send_notification_marks_notification_as_failed(
        self,
        mock_send_email,
    ):
        """
        A delivery exception should mark the notification as FAILED
        and persist the error message.
        """

        with self.assertRaises(RuntimeError):
            send_notification_task.run(
                notification_id=str(self.notification.id),
            )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification.status,
            NotificationStatus.FAILED,
        )

        self.assertIsNone(
            self.notification.sent_at,
        )

        self.assertEqual(
            self.notification.error_message,
            "Email delivery failed.",
        )

        mock_send_email.assert_called_once_with(
            self.notification,
        )

    @patch("apps.notifications.tasks.send_email_notification")
    def test_send_notification_is_idempotent_for_sent_notification(
        self,
        mock_send_email,
    ):
        """
        A notification that is already SENT should not be delivered
        again.
        """

        self.notification.status = NotificationStatus.SENT
        self.notification.save(
            update_fields=["status"],
        )

        send_notification_task.run(
            notification_id=str(self.notification.id),
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification.status,
            NotificationStatus.SENT,
        )

        mock_send_email.assert_not_called()

    @patch("apps.notifications.tasks.send_email_notification")
    def test_send_notification_clears_previous_error_on_success(
        self,
        mock_send_email,
    ):
        """
        A successful retry should clear a previous error message.
        """

        self.notification.status = NotificationStatus.PENDING
        self.notification.error_message = "Previous delivery failure."
        self.notification.save(
            update_fields=[
                "status",
                "error_message",
            ],
        )

        send_notification_task.run(
            notification_id=str(self.notification.id),
        )

        self.notification.refresh_from_db()

        self.assertEqual(
            self.notification.status,
            NotificationStatus.SENT,
        )

        self.assertEqual(
            self.notification.error_message,
            "",
        )

        self.assertIsNotNone(
            self.notification.sent_at,
        )

    @patch("apps.notifications.tasks.send_email_notification")
    def test_send_notification_task_is_registered_as_celery_task(
        self,
        mock_send_email,
    ):
        """
        The notification delivery function should be exposed as a
        Celery task through @shared_task.
        """

        self.assertTrue(
            hasattr(
                send_notification_task,
                "delay",
            ),
        )

        self.assertTrue(
            hasattr(
                send_notification_task,
                "apply_async",
            ),
        )