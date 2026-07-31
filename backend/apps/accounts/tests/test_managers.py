"""
Tests for the Accounts user manager.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserManagerTests(TestCase):
    """
    Test the custom UserManager.
    """

    def test_create_user_requires_email(self):
        """
        Email is mandatory when creating a user.
        """

        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="Password123!",
            )

    def test_email_is_normalized(self):
        """
        Email addresses should be normalized.
        """

        user = User.objects.create_user(
            email="TEST@Example.COM",
            password="Password123!",
        )

        self.assertEqual(
            user.email,
            "TEST@example.com",
        )

    def test_superuser_flags(self):
        """
        Superuser should have all required flags.
        """

        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="Password123!",
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_invalid_superuser(self):
        """
        Superuser cannot have is_staff=False.
        """

        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@example.com",
                password="Password123!",
                is_staff=False,
            )