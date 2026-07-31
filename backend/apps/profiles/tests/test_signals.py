"""
Tests for the Profiles signals.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.models import Profile

User = get_user_model()


class ProfileSignalTests(TestCase):
    """
    Tests for automatic profile creation signals.
    """

    def test_profile_created_when_user_created(self):
        """
        Creating a user should automatically create a profile.
        """

        user = User.objects.create_user(
            email="signal@example.com",
            password="Password123!",
        )

        self.assertTrue(
            Profile.objects.filter(
                user=user,
            ).exists()
        )

    def test_only_one_profile_created(self):
        """
        Saving an existing user should not create duplicate profiles.
        """

        user = User.objects.create_user(
            email="duplicate@example.com",
            password="Password123!",
        )

        user.first_name = "John"
        user.save()

        self.assertEqual(
            Profile.objects.filter(
                user=user,
            ).count(),
            1,
        )

    def test_profile_saved_with_user(self):
        """
        Saving a user should preserve the associated profile.
        """

        user = User.objects.create_user(
            email="save@example.com",
            password="Password123!",
        )

        profile = user.profile

        user.last_name = "Doe"
        user.save()

        profile.refresh_from_db()

        self.assertEqual(
            profile.user,
            user,
        )