from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AnalyticsViewPermissionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            password="pass1234",
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            password="pass1234",
            is_staff=True,
        )

    def test_regular_user_is_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)

        response = self.client.get(reverse("analytics:platform-summary"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_access_platform_summary(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(reverse("analytics:platform-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_trips", response.data)
        self.assertIn("agent_success_rate", response.data)

    def test_staff_user_can_access_agent_performance(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(reverse("analytics:agent-performance"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total", response.data)
        self.assertIn("pending_or_running", response.data)

    def test_unauthenticated_user_is_rejected(self):
        response = self.client.get(reverse("analytics:platform-summary"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
