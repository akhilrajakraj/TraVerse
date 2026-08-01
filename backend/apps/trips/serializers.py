"""
Serializers for the Trips application.
"""

from rest_framework import serializers

from apps.destinations.serializers import DestinationSerializer
from apps.trips.models import Trip


class TripSerializer(serializers.ModelSerializer):
    """
    Serializer for Trip objects.
    """

    destinations = DestinationSerializer(
        many=True,
        read_only=True,
    )

    destination_ids = serializers.PrimaryKeyRelatedField(
        source="destinations",
        many=True,
        queryset=Trip.destinations.field.related_model.objects.all(),
        write_only=True,
        required=False,
    )

    duration_days = serializers.ReadOnlyField()

    class Meta:
        model = Trip

        fields = (
            "id",
            "title",
            "start_date",
            "end_date",
            "duration_days",
            "status",
            "traveler_count",
            "notes",
            "computed_budget_total",
            "destinations",
            "destination_ids",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "status",
            "duration_days",
            "computed_budget_total",
            "created_at",
            "updated_at",
        )