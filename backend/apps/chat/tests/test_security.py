from datetime import date
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.trips.models import Trip


class ChatRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="chat-rate@example.com",
            password="pass1234",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title="Rate Limited Trip",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )
        self.url = reverse(
            "chat:chat",
            kwargs={"trip_id": self.trip.id},
        )
        self.client.force_authenticate(self.user)

    @patch("apps.chat.views.generate_chat_reply", return_value="reply")
    def test_31st_message_in_an_hour_is_rate_limited(self, mock_generate):
        for _ in range(30):
            response = self.client.post(
                self.url,
                {"message": "Hi"},
                format="json",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.url,
            {"message": "Hi"},
            format="json",
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data["error"]["code"], "rate_limited")
        self.assertEqual(mock_generate.call_count, 30)
