"""
Serializers for the Destinations application.
"""

from rest_framework import serializers

from apps.destinations.models import Destination


class DestinationSerializer(serializers.ModelSerializer):
    """
    Serializer for Destination objects.
    """

    class Meta:
        model = Destination

        fields = (
            "id",
            "name",
            "country",
            "city",
            "latitude",
            "longitude",
            "image_url",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )