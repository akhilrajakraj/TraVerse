"""
Destination search tool definition.

This module defines the interface used by the AI agent.
It does not access the Django ORM directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from decimal import Decimal


@dataclass(frozen=True)
class DestinationSearchResult:
    """
    Serializable destination search result.
    """

    name: str
    country: str
    city: str
    latitude: Decimal
    longitude: Decimal
    summary: str
    description: str
    tags: list[str]