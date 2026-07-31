"""
Tests for the Profiles models.
"""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.models import (
    Gender,
    Profile,
)

User = get_user_model()


class ProfileModelTests(TestCase):
    """
    Tests for the Profile model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

    def test_profile_created_by_signal(self):
        """
        A profile should be created automatically.
        """

        self.assertTrue(
            hasattr(
                self.user,
                "profile",
            )
        )

        self.assertIsInstance(
            self.user.profile,
            Profile,
        )

    def test_profile_uuid_primary_key(self):
        """
        Profile should use UUID as primary key.
        """

        self.assertIsInstance(
            self.user.profile.pk,
            uuid.UUID,
        )

    def test_profile_string_representation(self):
        """
        __str__ should return the user's email.
        """

        self.assertEqual(
            str(self.user.profile),
            self.user.email,
        )

    def test_profile_relationship(self):
        """
        User and Profile should have a OneToOne relationship.
        """

        self.assertEqual(
            self.user.profile.user,
            self.user,
        )

    def test_default_emergency_contact(self):
        """
        Emergency contact should default to an empty dictionary.
        """

        self.assertEqual(
            self.user.profile.emergency_contact,
            {},
        )

    def test_gender_choices(self):
        """
        Gender choices should expose expected values.
        """

        self.assertEqual(
            Gender.MALE,
            "male",
        )

        self.assertEqual(
            Gender.FEMALE,
            "female",
        )