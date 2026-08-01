"""
API views for the Itinerary application.
"""

from django.shortcuts import get_object_or_404

from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.destinations.models import Destination
from apps.itinerary import selectors
from apps.itinerary import services
from apps.itinerary.models import ItineraryDay
from apps.itinerary.serializers import (
    AddItineraryItemSerializer,
    ItineraryDaySerializer,
)
from apps.trips.models import Trip


class TripItineraryView(APIView):
    """
    Retrieve the complete itinerary for a trip.
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get(
        self,
        request,
        trip_id,
    ):
        trip = get_object_or_404(
            Trip,
            id=trip_id,
            user=request.user,
        )

        days = selectors.get_trip_itinerary(
            trip=trip,
        )

        serializer = ItineraryDaySerializer(
            days,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class AddItineraryItemView(APIView):
    """
    Append a new itinerary item to an itinerary day.
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(
        self,
        request,
        day_id,
    ):
        day = get_object_or_404(
            ItineraryDay.objects.select_related(
                "trip",
            ),
            id=day_id,
            trip__user=request.user,
        )

        serializer = AddItineraryItemSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        validated = serializer.validated_data

        destination = None

        destination_id = validated.get(
            "destination_id",
        )

        if destination_id:

            destination = get_object_or_404(
                Destination,
                id=destination_id,
                is_active=True,
            )

        item = services.add_item_to_day(
            day=day,
            title=validated["title"],
            description=validated.get(
                "description",
                "",
            ),
            start_time=validated.get(
                "start_time",
            ),
            estimated_cost_usd=validated.get(
                "estimated_cost_usd",
            ),
            destination=destination,
        )

        return Response(
            {
                "id": str(item.id),
                "message": (
                    "Itinerary item created successfully."
                ),
            },
            status=status.HTTP_201_CREATED,
        )