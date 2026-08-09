from decimal import Decimal
from typing import Optional

from apps.bookings.models import Booking, BookingType
from apps.recommendations.models import Recommendation
from apps.trips.models import Trip


def create_booking_intent(
    *,
    trip: Trip,
    booking_type: str,
    title: str,
    estimated_cost: Optional[Decimal] = None,
    notes: str = "",
    source_recommendation: Optional[Recommendation] = None,
) -> Booking:
    """Create a booking intent for an existing user-owned trip."""
    if booking_type not in BookingType.values:
        raise ValueError("Invalid booking type.")

    if source_recommendation is not None:
        if source_recommendation.trip_id != trip.id:
            raise ValueError(
                "Source recommendation must belong to the selected trip."
            )

    return Booking.objects.create(
        trip=trip,
        source_recommendation=source_recommendation,
        booking_type=booking_type,
        title=title,
        estimated_cost=estimated_cost,
        notes=notes,
    )
