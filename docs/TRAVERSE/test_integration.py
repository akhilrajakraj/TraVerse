from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.chat.models import ChatMessage, ChatRole, ChatSession
from apps.trips.models import Trip


class TestChatIntegration(APITestCase):
    """
    End-to-end integration tests for the Chat API.
    """

    def setUp(self):
        self.password = "Password123!"

        self.user = User.objects.create_user(
            email="john@example.com",
            password=self.password,
            first_name="John",
            last_name="Doe",
        )

        login = self.client.post(
            reverse("accounts:login"),
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            login.status_code,
            status.HTTP_200_OK,
        )

        self.token = login.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        today = timezone.now().date()

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=today,
            end_date=today + timedelta(days=6),
        )

        self.url = reverse(
            "chat:chat",
            kwargs={
                "trip_id": self.trip.id,
            },
        )