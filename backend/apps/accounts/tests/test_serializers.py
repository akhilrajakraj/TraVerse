"""
Tests for the Accounts serializers.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
)

User = get_user_model()


class RegisterSerializerTests(TestCase):
    """
    Tests for RegisterSerializer.
    """

    def test_register_serializer_creates_user(self):
        """
        Serializer should create a new user.
        """

        serializer = RegisterSerializer(
            data={
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "Password123!",
            }
        )

        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertEqual(
            user.email,
            "john@example.com",
        )

        self.assertTrue(
            user.check_password("Password123!")
        )

    def test_duplicate_email_fails(self):
        """
        Duplicate email addresses are not allowed.
        """

        User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

        serializer = RegisterSerializer(
            data={
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "password": "Password123!",
            }
        )

        self.assertFalse(serializer.is_valid())


class LoginSerializerTests(TestCase):
    """
    Tests for LoginSerializer.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

    def test_valid_login(self):
        """
        Valid credentials should authenticate.
        """

        serializer = LoginSerializer(
            data={
                "email": "john@example.com",
                "password": "Password123!",
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_invalid_password(self):
        """
        Invalid credentials should fail.
        """

        serializer = LoginSerializer(
            data={
                "email": "john@example.com",
                "password": "WrongPassword",
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_unknown_user(self):
        """
        Unknown email should fail authentication.
        """

        serializer = LoginSerializer(
            data={
                "email": "unknown@example.com",
                "password": "Password123!",
            }
        )

        self.assertFalse(serializer.is_valid())