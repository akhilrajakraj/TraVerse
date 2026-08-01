"""
API views for the Trips application.
"""

from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView

from apps.trips import services
from apps.trips.models import Trip
from apps.trips.permissions import IsTripOwner
from apps.trips.serializers import TripSerializer


class TripListCreateView(
    generics.ListCreateAPIView,
):
    """
    List the authenticated user's trips or create a new trip.
    """

    serializer_class = TripSerializer

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get_queryset(self):
        return Trip.objects.filter(
            user=self.request.user,
        ).prefetch_related(
            "destinations",
        )

    def perform_create(
        self,
        serializer,
    ):
        serializer.save(
            user=self.request.user,
        )


class TripRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update, or delete a single trip.
    """

    serializer_class = TripSerializer

    permission_classes = (
        permissions.IsAuthenticated,
        IsTripOwner,
    )

    def get_queryset(self):
        return Trip.objects.filter(
            user=self.request.user,
        ).prefetch_related(
            "destinations",
        )

    def perform_update(
        self,
        serializer,
    ):
        trip = serializer.instance

        services.update_trip_dates(
            trip=trip,
            start_date=serializer.validated_data.get(
                "start_date",
                trip.start_date,
            ),
            end_date=serializer.validated_data.get(
                "end_date",
                trip.end_date,
            ),
        )

        serializer.save()


class TripStatusUpdateView(APIView):
    """
    Transition a trip through its lifecycle.
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(
        self,
        request,
        pk,
    ):
        trip = get_object_or_404(
            Trip,
            pk=pk,
            user=request.user,
        )

        new_status = request.data.get(
            "status",
        )

        services.transition_trip_status(
            trip=trip,
            new_status=new_status,
        )

        return response.Response(
            TripSerializer(
                trip,
            ).data,
            status=status.HTTP_200_OK,
        )