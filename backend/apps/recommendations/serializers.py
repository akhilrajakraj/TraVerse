"""
Serializers for the Recommendations application.
"""

from rest_framework import serializers

from apps.destinations.serializers import DestinationSerializer
from apps.recommendations.models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    """
    Read serializer for recommendations.
    """

    destination = DestinationSerializer(
        read_only=True,
    )

    class Meta:
        model = Recommendation

        fields = [
            "id",
            "category",
            "score",
            "reason",
            "status",
            "is_ai_generated",
            "destination",
            "created_at",
        ]

        read_only_fields = fields