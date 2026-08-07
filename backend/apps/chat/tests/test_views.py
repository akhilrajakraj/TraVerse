"""
Unit tests for chat API views.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.chat.services import ChatService
from apps.trips.models import Trip


class ChatAPIViewTests(APITestCase):
    """
    Verify ChatAPIView.
    """

    def setUp(self) -> None:

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Adventure",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 20),
        )

        self.other_trip = Trip.objects.create(
            user=self.other_user,
            title="Paris Trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
        )

        self.url = reverse(
            "chat:chat",
            kwargs={
                "trip_id": self.trip.id,
            },
        )

    def test_authentication_required(self) -> None:
        """
        Anonymous users should be rejected.
        """

        response = self.client.post(
            self.url,
            {
                "message": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @patch("apps.chat.views.generate_chat_reply")
    def test_calls_generate_chat_reply(
        self,
        mock_generate,
    ) -> None:
        """
        The AI service should be invoked.
        """

        mock_generate.return_value = (
            "Hello traveller!"
        )

        self.client.force_authenticate(
            self.user,
        )

        response = self.client.post(
            self.url,
            {
                "message": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        mock_generate.assert_called_once_with(
            trip=self.trip,
            user_message="Hello",
        )

    @patch("apps.chat.views.generate_chat_reply")
    def test_returns_response_payload(
        self,
        mock_generate,
    ) -> None:
        """
        Response should contain the assistant reply.
        """

        mock_generate.return_value = (
            "Welcome!"
        )

        self.client.force_authenticate(
            self.user,
        )

        response = self.client.post(
            self.url,
            {
                "message": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.data["assistant_message"],
            "Welcome!",
        )

        self.assertIn(
            "session_id",
            response.data,
        )

        self.assertIn(
            "created_at",
            response.data,
        )

    def test_blank_message_returns_400(self) -> None:
        """
        Serializer validation should reject blanks.
        """

        self.client.force_authenticate(
            self.user,
        )

        response = self.client.post(
            self.url,
            {
                "message": "   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_user_cannot_access_other_trip(self) -> None:
        """
        Trips owned by another user should return 404.
        """

        self.client.force_authenticate(
            self.user,
        )

        url = reverse(
            "chat:chat",
            kwargs={
                "trip_id": self.other_trip.id,
            },
        )

        response = self.client.post(
            url,
            {
                "message": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch("apps.chat.views.generate_chat_reply")
    def test_active_session_is_returned(
        self,
        mock_generate,
    ) -> None:
        """
        Existing active session should be reused.
        """

        mock_generate.return_value = (
            "Hi!"
        )

        self.client.force_authenticate(
            self.user,
        )

        session = ChatService.get_or_create_active_session(
            trip=self.trip,
        )

        response = self.client.post(
            self.url,
            {
                "message": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            str(session.id),
            response.data["session_id"],
        )