"""
Tests for the Accounts models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    """
    Test the custom User model.
    """

    def test_create_user(self):
        """
        A regular user should be created successfully.
        """

        user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
            first_name="John",
            last_name="Doe",
        )

        self.assertEqual(
            user.email,
            "user@example.com",
        )

        self.assertTrue(
            user.check_password("Password123!")
        )

        self.assertFalse(
            user.is_staff,
        )

        self.assertFalse(
            user.is_superuser,
        )

    def test_create_superuser(self):
        """
        A superuser should be created successfully.
        """

        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin123!",
        )

        self.assertTrue(
            admin.is_staff,
        )

        self.assertTrue(
            admin.is_superuser,
        )

    def test_email_is_username_field(self):
        """
        Email should be the authentication identifier.
        """

        self.assertEqual(
            User.USERNAME_FIELD,
            "email",
        )

    def test_string_representation(self):
        """
        __str__ should return the user's email.
        """

        user = User.objects.create_user(
            email="alice@example.com",
            password="Password123!",
        )

        self.assertEqual(
            str(user),
            "alice@example.com",
        )

    def test_user_has_uuid_primary_key(self):
        """
        User should use UUID as its primary key.
        """

        import uuid

        user = User.objects.create_user(
            email="uuid@example.com",
            password="Password123!",
        )

        self.assertIsInstance(
            user.pk,
            uuid.UUID,
        )