"""
Destination search executor.

Bridges the AI layer and the Django ORM.
"""

from __future__ import annotations

from ai.tools.destination_search import DestinationSearchResult

from apps.destinations.selectors import search_destinations


def search_destination(
    *,
    query: str,
) -> list[DestinationSearchResult]:
    """
    Search destinations and convert them into AI-safe objects.
    """

    results: list[DestinationSearchResult] = []

    for destination in search_destinations(
        query=query,
    ):
        results.append(
            DestinationSearchResult(
                name=destination.name,
                country=destination.country,
                city=destination.city,
                latitude=destination.latitude,
                longitude=destination.longitude,
                summary=destination.summary,
                description=destination.description,
                tags=destination.tags,
            )
        )

    return results