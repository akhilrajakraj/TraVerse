"""
Tests for the Profiles serializers.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.profiles.serializers import ProfileSerializer

User = get_user_model()


class ProfileSerializerTests(TestCase):
    """
    Tests for ProfileSerializer.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="john@example.com",
            password="Password123!",
        )

        self.profile = self.user.profile

    def test_serializer_contains_expected_fields(self):
        """
        Serializer should expose the expected fields.
        """

        serializer = ProfileSerializer(self.profile)

        expected_fields = {
            "id",
            "user",
            "phone_number",
            "date_of_birth",
            "gender",
            "profile_picture",
            "bio",
            "emergency_contact",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(serializer.data.keys()),
            expected_fields,
        )

    def test_profile_update(self):
        """
        Editable fields should be updated successfully.
        """

        serializer = ProfileSerializer(
            instance=self.profile,
            data={
                "phone_number": "9876543210",
                "bio": "Travel enthusiast",
                "gender": "male",
                "emergency_contact": {
                    "name": "Jane",
                    "phone": "9999999999",
                },
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid())

        profile = serializer.save()

        self.assertEqual(
            profile.phone_number,
            "9876543210",
        )

        self.assertEqual(
            profile.bio,
            "Travel enthusiast",
        )

        self.assertEqual(
            profile.gender,
            "male",
        )

    def test_read_only_fields_are_protected(self):
        """
        Read-only fields should not be writable.
        """

        serializer = ProfileSerializer(
            instance=self.profile,
            data={
                "id": "123",
                "user": None,
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid())

        profile = serializer.save()

        self.assertEqual(
            profile.user,
            self.user,
        )