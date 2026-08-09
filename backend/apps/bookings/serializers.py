from rest_framework import serializers

from apps.bookings.models import Booking, BookingType
from apps.recommendations.models import Recommendation


class BookingSerializer(serializers.ModelSerializer):
    source_recommendation = serializers.PrimaryKeyRelatedField(
        queryset=Recommendation.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Booking
        fields = (
            "id",
            "booking_type",
            "status",
            "title",
            "estimated_cost",
            "notes",
            "source_recommendation",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "updated_at",
        )

    def validate_booking_type(self, value):
        if value not in BookingType.values:
            raise serializers.ValidationError("Invalid booking type.")
        return value
