"""
Reusable database queries for the Destinations application.

Selectors contain read-only ORM queries that may be reused by:

- API Views
- AI Retrieval
- Future recommendation engines
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from apps.destinations.models import Destination


def search_destinations(*, query: str) -> QuerySet[Destination]:
    """
    Search active destinations by name, country, city or descriptive metadata.

    An empty query intentionally returns the active catalog so the same
    endpoint supports both browsing and search.
    """

    query = query.strip()

    destinations = Destination.objects.filter(is_active=True)

    if not query:
        return destinations.order_by("country", "city", "name")

    return destinations.filter(
        Q(name__icontains=query)
        | Q(country__icontains=query)
        | Q(city__icontains=query)
        | Q(summary__icontains=query)
        | Q(description__icontains=query)
        | Q(tags__icontains=query)
    ).order_by("country", "city", "name")
