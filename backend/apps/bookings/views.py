from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, response, status

from apps.bookings import services
from apps.bookings.models import Booking
from apps.bookings.serializers import BookingSerializer
from apps.trips.models import Trip


class TripBookingListCreateView(generics.ListCreateAPIView):
    """List or create booking intents belonging to the authenticated trip."""

    serializer_class = BookingSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_trip(self):
        return get_object_or_404(
            Trip,
            pk=self.kwargs["trip_pk"],
            user=self.request.user,
        )

    def get_queryset(self):
        return Booking.objects.filter(
            trip=self.get_trip(),
        ).select_related("source_recommendation")

    def create(self, request, *args, **kwargs):
        trip = self.get_trip()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            booking = services.create_booking_intent(
                trip=trip,
                booking_type=serializer.validated_data["booking_type"],
                title=serializer.validated_data["title"],
                estimated_cost=serializer.validated_data.get("estimated_cost"),
                notes=serializer.validated_data.get("notes", ""),
                source_recommendation=serializer.validated_data.get(
                    "source_recommendation"
                ),
            )
        except ValueError as exc:
            return response.Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output = self.get_serializer(booking)
        return response.Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )
