"""
Model tests for the Notifications application.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


User = get_user_model()


class NotificationModelTests(TestCase):
    """
    Test suite for Notification domain model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

    def create_notification(self, **kwargs):
        """
        Create a notification using valid default values.
        """

        defaults = {
            "user": self.user,
            "notification_type": NotificationType.TRIP_PLAN_READY,
            "channel": NotificationChannel.EMAIL,
            "subject": "Trip plan ready",
            "body": "Your trip plan is ready.",
        }

        defaults.update(kwargs)

        return Notification.objects.create(
            **defaults,
        )

    def test_notification_is_created_for_user(self):
        """
        Notifications should be associated with the correct user.
        """

        notification = self.create_notification()

        self.assertEqual(
            notification.user,
            self.user,
        )

        self.assertEqual(
            Notification.objects.count(),
            1,
        )

    def test_notification_uses_uuid_primary_key(self):
        """
        Notifications should use a UUID primary key.
        """

        notification = self.create_notification()

        self.assertIsNotNone(
            notification.id,
        )

        self.assertEqual(
            notification.id.__class__.__name__,
            "UUID",
        )

    def test_notification_defaults(self):
        """
        New notifications should use the expected default values.
        """

        notification = self.create_notification()

        self.assertEqual(
            notification.channel,
            NotificationChannel.EMAIL,
        )

        self.assertEqual(
            notification.status,
            NotificationStatus.PENDING,
        )

        self.assertFalse(
            notification.is_read,
        )

        self.assertIsNone(
            notification.sent_at,
        )

        self.assertEqual(
            notification.error_message,
            "",
        )

    def test_notification_supports_all_notification_types(self):
        """
        Every declared notification type should be accepted by the model.
        """

        notification_types = [
            NotificationType.TRIP_PLAN_READY,
            NotificationType.TRIP_PLAN_FAILED,
            NotificationType.SHARE_LINK_CREATED,
            NotificationType.GENERIC,
        ]

        for notification_type in notification_types:
            notification = self.create_notification(
                notification_type=notification_type,
            )

            self.assertEqual(
                notification.notification_type,
                notification_type,
            )

    def test_notification_status_can_transition_to_sent(self):
        """
        A notification should support the SENT delivery status.
        """

        notification = self.create_notification(
            status=NotificationStatus.SENT,
            sent_at=timezone.now(),
        )

        self.assertEqual(
            notification.status,
            NotificationStatus.SENT,
        )

        self.assertIsNotNone(
            notification.sent_at,
        )

    def test_notification_status_can_transition_to_failed(self):
        """
        A notification should support the FAILED delivery status
        and store an error message.
        """

        notification = self.create_notification(
            status=NotificationStatus.FAILED,
            error_message="Email delivery failed.",
        )

        self.assertEqual(
            notification.status,
            NotificationStatus.FAILED,
        )

        self.assertEqual(
            notification.error_message,
            "Email delivery failed.",
        )

    def test_notification_can_be_marked_as_read(self):
        """
        Notifications should support read/unread state.
        """

        notification = self.create_notification()

        self.assertFalse(
            notification.is_read,
        )

        notification.is_read = True
        notification.save(
            update_fields=["is_read"],
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read,
        )

    def test_notification_has_timestamps(self):
        """
        Notifications should receive created_at and updated_at
        timestamps from TimeStampedModel.
        """

        notification = self.create_notification()

        self.assertIsNotNone(
            notification.created_at,
        )

        self.assertIsNotNone(
            notification.updated_at,
        )

    def test_notification_string_representation(self):
        """
        Notification.__str__ should include the notification type,
        user email, and status.
        """

        notification = self.create_notification()

        self.assertEqual(
            str(notification),
            (
                f"{NotificationType.TRIP_PLAN_READY}"
                f" -> {self.user.email}"
                f" ({NotificationStatus.PENDING})"
            ),
        )

    def test_notifications_are_ordered_by_newest_first(self):
        """
        Notifications should be ordered by created_at descending.
        """

        older = self.create_notification(
            subject="Older notification",
        )

        newer = self.create_notification(
            subject="Newer notification",
        )

        notifications = list(
            Notification.objects.all(),
        )

        self.assertEqual(
            notifications[0],
            newer,
        )

        self.assertEqual(
            notifications[1],
            older,
        )

    def test_user_can_have_multiple_notifications(self):
        """
        A user should be able to own multiple notifications.
        """

        self.create_notification(
            subject="First notification",
        )

        self.create_notification(
            subject="Second notification",
        )

        self.assertEqual(
            self.user.notifications.count(),
            2,
        )

    def test_notification_is_deleted_when_user_is_deleted(self):
        """
        Deleting the owning user should cascade to their notifications.
        """

        notification = self.create_notification()

        notification_id = notification.id

        self.user.delete()

        self.assertFalse(
            Notification.objects.filter(
                id=notification_id,
            ).exists(),
        )