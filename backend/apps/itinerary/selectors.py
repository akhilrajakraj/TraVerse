"""
Read-side query helpers for the Itinerary application.

Selectors contain optimized database queries that shape data for a
specific consumer without modifying application state.
"""

from __future__ import annotations

from django.db.models import Prefetch

from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)
from apps.trips.models import Trip


def get_trip_itinerary(
    *,
    trip: Trip,
) -> list[ItineraryDay]:
    """
    Return every itinerary day for a trip with all itinerary items
    prefetched in the correct order.

    Query plan:

    - 1 query for itinerary days.
    - 1 query for all itinerary items.
    - Destination objects are loaded through select_related.

    Total: 2 database queries regardless of trip size.
    """

    items_prefetch = Prefetch(
        "items",
        queryset=(
            ItineraryItem.objects
            .select_related("destination")
            .order_by("order")
        ),
    )

    return list(
        trip.itinerary_days
        .prefetch_related(items_prefetch)
        .order_by("day_number")
    )