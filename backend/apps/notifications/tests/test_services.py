"""
Service tests for the Notifications application.
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
from apps.notifications.services import (
    create_notification,
    mark_as_read,
)


User = get_user_model()


class NotificationServiceTests(TestCase):
    """
    Test suite for Notification services.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_create_notification(self, mock_delay):
        """
        Service should create a pending notification and enqueue
        asynchronous delivery.
        """

        notification = create_notification(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            subject="Trip plan ready",
            body="Your trip plan is ready.",
        )

        self.assertIsNotNone(
            notification,
        )

        self.assertEqual(
            notification.user,
            self.user,
        )

        self.assertEqual(
            notification.notification_type,
            NotificationType.TRIP_PLAN_READY,
        )

        self.assertEqual(
            notification.channel,
            NotificationChannel.EMAIL,
        )

        self.assertEqual(
            notification.subject,
            "Trip plan ready",
        )

        self.assertEqual(
            notification.body,
            "Your trip plan is ready.",
        )

        self.assertEqual(
            notification.status,
            NotificationStatus.PENDING,
        )

        self.assertFalse(
            notification.is_read,
        )

        mock_delay.assert_called_once_with(
            notification_id=str(notification.id),
        )

    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_create_notification_persists_notification(self, mock_delay):
        """
        Service should persist the notification in the database.
        """

        notification = create_notification(
            user=self.user,
            notification_type=NotificationType.GENERIC,
            subject="Test notification",
            body="Test notification body.",
        )

        persisted = Notification.objects.get(
            pk=notification.pk,
        )

        self.assertEqual(
            persisted.user,
            self.user,
        )

        self.assertEqual(
            persisted.notification_type,
            NotificationType.GENERIC,
        )

        self.assertEqual(
            persisted.subject,
            "Test notification",
        )

        self.assertEqual(
            persisted.body,
            "Test notification body.",
        )

        self.assertEqual(
            persisted.status,
            NotificationStatus.PENDING,
        )

        mock_delay.assert_called_once()

    @patch("apps.notifications.tasks.send_notification_task.delay")
    def test_create_notification_accepts_explicit_channel(
        self,
        mock_delay,
    ):
        """
        Service should accept an explicitly supplied notification
        channel.
        """

        notification = create_notification(
            user=self.user,
            notification_type=NotificationType.SHARE_LINK_CREATED,
            subject="Share link created",
            body="Your share link was created.",
            channel=NotificationChannel.EMAIL,
        )

        self.assertEqual(
            notification.channel,
            NotificationChannel.EMAIL,
        )

        mock_delay.assert_called_once_with(
            notification_id=str(notification.id),
        )

    def test_mark_as_read(self):
        """
        Service should mark an unread notification as read.
        """

        notification = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            channel=NotificationChannel.EMAIL,
            subject="Trip plan ready",
            body="Your trip plan is ready.",
            status=NotificationStatus.PENDING,
        )

        self.assertFalse(
            notification.is_read,
        )

        result = mark_as_read(
            notification=notification,
        )

        self.assertEqual(
            result.pk,
            notification.pk,
        )

        self.assertTrue(
            result.is_read,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )

    def test_mark_as_read_does_not_change_delivery_status(self):
        """
        Marking a notification as read should not modify its delivery
        status.
        """

        notification = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            channel=NotificationChannel.EMAIL,
            subject="Trip plan ready",
            body="Your trip plan is ready.",
            status=NotificationStatus.SENT,
        )

        result = mark_as_read(
            notification=notification,
        )

        self.assertTrue(
            result.is_read,
        )

        self.assertEqual(
            result.status,
            NotificationStatus.SENT,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )

        self.assertEqual(
            notification.status,
            NotificationStatus.SENT,
        )

    def test_mark_as_read_is_idempotent(self):
        """
        Marking an already-read notification as read should remain
        successful and should not change its state incorrectly.
        """

        notification = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.GENERIC,
            channel=NotificationChannel.EMAIL,
            subject="Already read",
            body="This notification is already read.",
            status=NotificationStatus.SENT,
            is_read=True,
        )

        result = mark_as_read(
            notification=notification,
        )

        self.assertEqual(
            result.pk,
            notification.pk,
        )

        self.assertTrue(
            result.is_read,
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )