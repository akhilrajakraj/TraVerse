"""
Serializers for the Itinerary application.
"""

from rest_framework import serializers

from apps.destinations.models import Destination
from apps.destinations.serializers import DestinationSerializer
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)


class ItineraryItemSerializer(serializers.ModelSerializer):
    """
    Read serializer for itinerary items.
    """

    destination = DestinationSerializer(
        read_only=True,
    )

    destination_id = serializers.PrimaryKeyRelatedField(
        source="destination",
        queryset=Destination.objects.filter(
            is_active=True,
        ),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ItineraryItem

        fields = [
            "id",
            "order",
            "title",
            "description",
            "start_time",
            "estimated_cost_usd",
            "is_ai_generated",
            "destination",
            "destination_id",
        ]

        read_only_fields = [
            "id",
            "order",
            "is_ai_generated",
        ]


class ItineraryDaySerializer(serializers.ModelSerializer):
    """
    Read serializer for itinerary days.
    """

    items = ItineraryItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ItineraryDay

        fields = [
            "id",
            "date",
            "day_number",
            "summary",
            "weather_condition",
            "weather_high_f",
            "weather_low_f",
            "weather_precipitation_chance",
            "items",
        ]

        read_only_fields = [
            "id",
            "day_number",
            "weather_condition",
            "weather_high_f",
            "weather_low_f",
            "weather_precipitation_chance",
        ]


class AddItineraryItemSerializer(serializers.Serializer):
    """
    Serializer used when adding a new itinerary item.

    Ordering is intentionally controlled by the service layer.
    """

    title = serializers.CharField(
        max_length=200,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    start_time = serializers.TimeField(
        required=False,
        allow_null=True,
    )

    estimated_cost_usd = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    destination_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )
