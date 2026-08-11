"""
Views for the Destinations application.
"""

from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from apps.core.permissions import IsStaffOrReadOnly
from apps.destinations.models import Destination
from apps.destinations.selectors import search_destinations
from apps.destinations.serializers import DestinationSerializer


class DestinationPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 48


class DestinationListView(generics.ListCreateAPIView):
    """
    Browse active destinations or search the same catalog by query text.

    GET /destinations/ returns the active catalog.
    GET /destinations/?search=tokyo filters by name, country, city,
    summary, description or tags.
    """

    serializer_class = DestinationSerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class = DestinationPagination

    def get_queryset(self):
        return search_destinations(query=self.request.query_params.get("search", ""))


class DestinationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a destination.
    """

    serializer_class = DestinationSerializer
    permission_classes = [IsStaffOrReadOnly]
    queryset = Destination.objects.all()
