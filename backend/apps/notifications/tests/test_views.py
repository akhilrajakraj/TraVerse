"""
API view tests for the Notifications application.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from apps.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


User = get_user_model()


class NotificationViewTests(TestCase):
    """
    Test suite for Notifications API views.
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

        self.notification = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            channel=NotificationChannel.EMAIL,
            subject="Trip plan ready",
            body="Your trip plan is ready.",
            status=NotificationStatus.PENDING,
        )

        self.read_notification = Notification.objects.create(
            user=self.user,
            notification_type=NotificationType.GENERIC,
            channel=NotificationChannel.EMAIL,
            subject="Read notification",
            body="This notification has already been read.",
            status=NotificationStatus.SENT,
            is_read=True,
        )

        self.other_user_notification = Notification.objects.create(
            user=self.other_user,
            notification_type=NotificationType.GENERIC,
            channel=NotificationChannel.EMAIL,
            subject="Private notification",
            body="This belongs to another user.",
            status=NotificationStatus.SENT,
        )

        self.list_url = reverse(
            "notifications:notification-list",
        )

    def test_notification_list_requires_authentication(self):
        """
        Notification list should require authentication.
        """

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_list_own_notifications(self):
        """
        Authenticated users should receive only their own notifications.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

        returned_ids = {
            item["id"]
            for item in response.data
        }

        self.assertIn(
            str(self.notification.id),
            returned_ids,
        )

        self.assertIn(
            str(self.read_notification.id),
            returned_ids,
        )

        self.assertNotIn(
            str(self.other_user_notification.id),
            returned_ids,
        )

    def test_notification_list_returns_only_unread_notifications(
        self,
    ):
        """
        ?unread=true should return only unread notifications.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.list_url,
            {"unread": "true"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            str(self.notification.id),
        )

    def test_notification_list_does_not_return_other_users_notifications(
        self,
    ):
        """
        A user must never receive another user's notifications.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        response = self.client.get(
            self.list_url,
        )

        returned_ids = {
            item["id"]
            for item in response.data
        }

        self.assertNotIn(
            str(self.other_user_notification.id),
            returned_ids,
        )

    def test_notification_list_for_user_with_no_notifications(
        self,
    ):
        """
        A user without notifications should receive an empty list.
        """

        new_user = User.objects.create_user(
            email="empty@example.com",
            password="Password123!",
        )

        self.client.force_authenticate(
            user=new_user,
        )

        response = self.client.get(
            self.list_url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data,
            [],
        )

    def test_mark_notification_as_read_requires_authentication(
        self,
    ):
        """
        Mark-read endpoint should require authentication.
        """

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": self.notification.id,
            },
        )

        response = self.client.post(
            url,
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_authenticated_user_can_mark_own_notification_as_read(
        self,
    ):
        """
        An authenticated user should be able to mark their own
        notification as read.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": self.notification.id,
            },
        )

        response = self.client.post(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.notification.refresh_from_db()

        self.assertTrue(
            self.notification.is_read,
        )

        self.assertEqual(
            response.data["id"],
            str(self.notification.id),
        )

    def test_user_cannot_mark_another_users_notification_as_read(
        self,
    ):
        """
        A user must not be able to mark another user's notification
        as read.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": self.other_user_notification.id,
            },
        )

        response = self.client.post(
            url,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.other_user_notification.refresh_from_db()

        self.assertFalse(
            self.other_user_notification.is_read,
        )

    def test_mark_read_returns_serialized_notification(
        self,
    ):
        """
        Mark-read should return the updated serialized notification.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": self.notification.id,
            },
        )

        response = self.client.post(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["id"],
            str(self.notification.id),
        )

        self.assertEqual(
            response.data["is_read"],
            True,
        )

    def test_mark_read_is_idempotent(self):
        """
        Marking an already-read notification as read should remain
        successful.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": self.read_notification.id,
            },
        )

        response = self.client.post(
            url,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.read_notification.refresh_from_db()

        self.assertTrue(
            self.read_notification.is_read,
        )

    def test_unknown_notification_returns_404(
        self,
    ):
        """
        Mark-read should return 404 for an unknown notification UUID.
        """

        self.client.force_authenticate(
            user=self.user,
        )

        import uuid

        url = reverse(
            "notifications:notification-mark-read",
            kwargs={
                "notification_pk": uuid.uuid4(),
            },
        )

        response = self.client.post(
            url,
        )

        self.assertEqual(
            response.status_code,
            404,
        )