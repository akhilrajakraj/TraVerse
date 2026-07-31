"""
Serializers for the Profiles application.
"""

from rest_framework import serializers

from apps.profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profiles.
    """

    class Meta:
        model = Profile

        fields = (
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
        )

        read_only_fields = (
            "id",
            "user",
            "created_at",
            "updated_at",
        )