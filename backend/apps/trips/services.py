"""
Business logic for the Trips application.

RULE:
This module must never import anything from rest_framework or
django.http.

It accepts plain Python values and Django ORM model instances,
returns Django model instances, or raises application-level
exceptions.

This design keeps the service layer completely independent from
HTTP concerns and allows direct unit testing without DRF.
"""

from datetime import date

from apps.trips.exceptions import (
    InvalidDateRange,
    InvalidStatusTransition,
)
from apps.trips.models import (
    Trip,
    TripStatus,
)


# Defines every legal lifecycle transition.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    TripStatus.DRAFT: {
        TripStatus.PLANNING,
        TripStatus.CANCELLED,
    },
    TripStatus.PLANNING: {
        TripStatus.PLANNED,
        TripStatus.DRAFT,
        TripStatus.CANCELLED,
    },
    TripStatus.PLANNED: {
        TripStatus.COMPLETED,
        TripStatus.CANCELLED,
    },
    TripStatus.COMPLETED: set(),
    TripStatus.CANCELLED: set(),
}


def validate_date_range(
    start_date: date,
    end_date: date,
) -> None:
    """
    Ensure that a trip's date range is valid.
    """

    if end_date < start_date:
        raise InvalidDateRange()


def create_trip(
    *,
    user,
    title: str,
    start_date: date,
    end_date: date,
    destination_ids: list[int] | None = None,
    traveler_count: int = 1,
    notes: str = "",
) -> Trip:
    """
    Create a new Trip.

    The authenticated user is always supplied by the caller and
    is never accepted from client input.
    """

    validate_date_range(
        start_date,
        end_date,
    )

    trip = Trip.objects.create(
        user=user,
        title=title,
        start_date=start_date,
        end_date=end_date,
        traveler_count=traveler_count,
        notes=notes,
        status=TripStatus.DRAFT,
    )

    if destination_ids:
        trip.destinations.set(
            destination_ids,
        )

    return trip


def update_trip_dates(
    *,
    trip: Trip,
    start_date: date,
    end_date: date,
) -> Trip:
    """
    Update a trip's travel dates.
    """

    validate_date_range(
        start_date,
        end_date,
    )

    trip.start_date = start_date
    trip.end_date = end_date

    trip.save(
        update_fields=[
            "start_date",
            "end_date",
            "updated_at",
        ],
    )

    return trip


def transition_trip_status(
    *,
    trip: Trip,
    new_status: str,
) -> Trip:
    """
    Move a trip through its lifecycle.
    """

    allowed = _ALLOWED_TRANSITIONS.get(
        trip.status,
        set(),
    )

    if new_status not in allowed:
        raise InvalidStatusTransition(
            message=(
                f"Cannot move trip from "
                f"'{trip.status}' "
                f"to "
                f"'{new_status}'."
            ),
        )

    trip.status = new_status

    trip.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    return trip