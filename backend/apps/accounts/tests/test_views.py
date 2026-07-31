"""
Tests for the Accounts API views.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterViewTests(APITestCase):
    """
    Tests for the registration endpoint.
    """

    def test_register_user(self):
        """
        A new user should be registered successfully.
        """

        response = self.client.post(
            "/api/accounts/register/",
            {
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "Password123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            User.objects.filter(
                email="john@example.com"
            ).exists()
        )


class LoginViewTests(APITestCase):
    """
    Tests for the login endpoint.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

    def test_login_success(self):
        """
        Valid credentials should return JWT tokens.
        """

        response = self.client.post(
            "/api/accounts/login/",
            {
                "email": "john@example.com",
                "password": "Password123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_login_invalid_credentials(self):
        """
        Invalid credentials should return 400.
        """

        response = self.client.post(
            "/api/accounts/login/",
            {
                "email": "john@example.com",
                "password": "WrongPassword",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class MeViewTests(APITestCase):
    """
    Tests for the authenticated user endpoint.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

    def test_me_requires_authentication(self):
        """
        Anonymous users should not access /me/.
        """

        response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )