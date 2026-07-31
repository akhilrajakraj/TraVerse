"""
Tests for the Profiles API views.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ProfileMeViewTests(APITestCase):
    """
    Tests for the authenticated profile endpoint.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

        refresh = RefreshToken.for_user(self.user)

        self.access_token = str(refresh.access_token)

    def authenticate(self):
        """
        Authenticate the test client.
        """

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

    def test_me_requires_authentication(self):
        """
        Anonymous users should not access the endpoint.
        """

        response = self.client.get(
            "/api/profiles/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_view_profile(self):
        """
        Authenticated users should retrieve their profile.
        """

        self.authenticate()

        response = self.client.get(
            "/api/profiles/me/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            str(response.data["user"]),
            str(self.user.id),
        )

    def test_authenticated_user_can_update_profile(self):
        """
        Authenticated users should update their profile.
        """

        self.authenticate()

        response = self.client.patch(
            "/api/profiles/me/",
            {
                "phone_number": "9876543210",
                "bio": "Traveler",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.profile.refresh_from_db()

        self.assertEqual(
            self.user.profile.phone_number,
            "9876543210",
        )

        self.assertEqual(
            self.user.profile.bio,
            "Traveler",
        )