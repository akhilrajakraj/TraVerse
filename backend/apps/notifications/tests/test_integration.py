"""
Integration tests for the Notifications application.

These tests verify that the main notification components work together:

    service -> database -> Celery task -> delivery lifecycle -> API

The Celery task is executed synchronously with ``.run()`` so the tests do
not require a running Celery worker or broker. Email delivery itself is
mocked because the email backend has its own dedicated unit tests.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.services import create_notification
from apps.notifications.tasks import send_notification_task


User = get_user_model()


class NotificationIntegrationTests(TestCase):
    """
    Test the complete notification workflow across application layers.
    """

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Password123!",
        )

        self.list_url = reverse(
            "notifications:notification-list",
        )

    @patch("apps.notifications.tasks.send_email_notification")
    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_notification_complete_lifecycle(
        self,
        mock_delay,
        mock_send_email,
    ):
        """
        A notification should move through the complete application flow:

            create_notification()
                -> PENDING
                -> Celery task dispatched
                -> delivery performed
                -> SENT
                -> visible through authenticated API
                -> marked as read
                -> is_read=True
        """

        # --------------------------------------------------------------
        # 1. Create the notification through the service layer.
        # --------------------------------------------------------------
        notification = create_notification(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            subject="Trip plan ready",
            body="Your trip plan is ready.",
            channel=NotificationChannel.EMAIL,
        )

        self.assertIsNotNone(notification)

        # The service creates the database record before dispatching it.
        self.assertEqual(
            notification.status,
            NotificationStatus.PENDING,
        )
        self.assertFalse(notification.is_read)

        persisted = Notification.objects.get(
            pk=notification.pk,
        )

        self.assertEqual(persisted.user, self.user)
        self.assertEqual(
            persisted.notification_type,
            NotificationType.TRIP_PLAN_READY,
        )
        self.assertEqual(persisted.subject, "Trip plan ready")
        self.assertEqual(
            persisted.body,
            "Your trip plan is ready.",
        )

        # The service must enqueue the notification using its UUID.
        mock_delay.assert_called_once_with(
            notification_id=str(notification.id),
        )

        # --------------------------------------------------------------
        # 2. Execute the delivery task synchronously.
        #
        # We patch the email backend because the backend itself is
        # already covered by test_backends.py.
        # --------------------------------------------------------------
        send_notification_task.run(
            notification_id=str(notification.id),
        )

        notification.refresh_from_db()

        mock_send_email.assert_called_once_with(
            notification,
        )

        # Successful delivery must transition PENDING -> SENT.
        self.assertEqual(
            notification.status,
            NotificationStatus.SENT,
        )
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(notification.error_message, "")

        # --------------------------------------------------------------
        # 3. Retrieve the delivered notification through the API.
        # --------------------------------------------------------------
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        serialized = response.data[0]

        self.assertEqual(
            serialized["id"],
            str(notification.id),
        )
        self.assertEqual(
            serialized["notification_type"],
            NotificationType.TRIP_PLAN_READY,
        )
        self.assertEqual(
            serialized["subject"],
            "Trip plan ready",
        )
        self.assertEqual(
            serialized["body"],
            "Your trip plan is ready.",
        )
        self.assertEqual(
            serialized["status"],
            NotificationStatus.SENT,
        )
        self.assertFalse(serialized["is_read"])

        # --------------------------------------------------------------
        # 4. Mark the same notification as read through the API.
        # --------------------------------------------------------------
        mark_read_url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": notification.id,
            },
        )

        mark_read_response = self.client.post(
            mark_read_url,
        )

        self.assertEqual(
            mark_read_response.status_code,
            200,
        )

        self.assertEqual(
            mark_read_response.data["id"],
            str(notification.id),
        )
        self.assertTrue(
            mark_read_response.data["is_read"],
        )

        # --------------------------------------------------------------
        # 5. Verify the final database state.
        # --------------------------------------------------------------
        notification.refresh_from_db()

        self.assertEqual(
            notification.status,
            NotificationStatus.SENT,
        )
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.sent_at)

    @patch("apps.notifications.tasks.send_email_notification")
    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_notification_failure_is_excluded_from_successful_delivery_flow(
        self,
        mock_delay,
        mock_send_email,
    ):
        """
        A delivery failure should be persisted by the task and should not
        incorrectly appear as a successful SENT notification.

        The service still creates the notification as PENDING and queues
        the task; the task owns the transition to FAILED.
        """

        mock_send_email.side_effect = RuntimeError(
            "Email delivery failed.",
        )

        notification = create_notification(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_FAILED,
            subject="Trip plan failed",
            body="Your trip plan could not be generated.",
        )

        self.assertEqual(
            notification.status,
            NotificationStatus.PENDING,
        )

        mock_delay.assert_called_once_with(
            notification_id=str(notification.id),
        )

        # The task records FAILED and re-raises so Celery can retry.
        with self.assertRaises(RuntimeError) as context:
            send_notification_task.run(
                notification_id=str(notification.id),
            )

        self.assertEqual(
            str(context.exception),
            "Email delivery failed.",
        )

        notification.refresh_from_db()

        self.assertEqual(
            notification.status,
            NotificationStatus.FAILED,
        )
        self.assertIsNone(notification.sent_at)
        self.assertEqual(
            notification.error_message,
            "Email delivery failed.",
        )

        # The notification remains owned by the correct user and is still
        # unread because delivery failure does not mark it as read.
        self.assertEqual(
            notification.user,
            self.user,
        )
        self.assertFalse(notification.is_read)

        # It should still be retrievable by its owner through the API.
        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["id"],
            str(notification.id),
        )
        self.assertEqual(
            response.data[0]["status"],
            NotificationStatus.FAILED,
        )
        self.assertFalse(
            response.data[0]["is_read"],
        )

        # Another user must not receive the notification.
        self.client.force_authenticate(
            user=self.other_user,
        )

        other_user_response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            other_user_response.status_code,
            200,
        )
        self.assertEqual(
            other_user_response.data,
            [],
        )