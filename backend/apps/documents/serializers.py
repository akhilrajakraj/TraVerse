from rest_framework import serializers

from apps.documents.models import Document
from apps.itinerary.serializers import ItineraryDaySerializer


class ShareLinkSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "share_url",
            "is_active",
            "expires_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_share_url(
        self,
        obj: Document,
    ) -> str:
        return f"/api/v1/public/share/{obj.share_token}/"


class PublicItinerarySerializer(serializers.Serializer):
    """
    Deliberately minimal serializer for public shared itineraries.

    Only fields that are safe for an unauthenticated visitor
    are exposed.
    """

    trip_title = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    days = ItineraryDaySerializer(
        many=True,
    )