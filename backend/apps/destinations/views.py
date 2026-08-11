"""
Views for the Destinations application.
"""

from rest_framework import generics

from apps.core.permissions import IsStaffOrReadOnly
from apps.destinations.models import Destination
from apps.destinations.serializers import DestinationSerializer


class DestinationListView(generics.ListCreateAPIView):
    """
    List all active destinations or create a new destination.
    """

    serializer_class = DestinationSerializer

    permission_classes = [
        IsStaffOrReadOnly,
    ]

    queryset = Destination.objects.filter(
        is_active=True,
    ).order_by(
        "country",
        "city",
        "name",
    )


class DestinationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a destination.
    """

    serializer_class = DestinationSerializer

    permission_classes = [
        IsStaffOrReadOnly,
    ]

    queryset = Destination.objects.all()
