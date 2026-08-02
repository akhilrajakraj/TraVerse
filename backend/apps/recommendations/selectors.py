"""
Read-only query selectors for the Recommendations application.
"""

from django.db.models import QuerySet

from apps.recommendations.models import (
    Recommendation,
    RecommendationStatus,
)
from apps.trips.models import Trip


def get_trip_recommendations(
    trip: Trip,
) -> QuerySet[Recommendation]:
    """
    Return all recommendations belonging to a trip.

    Recommendations are ordered according to the model's default
    ordering (highest score first).
    """

    return Recommendation.objects.filter(
        trip=trip,
    ).select_related(
        "destination",
    )


def get_pending_recommendations(
    trip: Trip,
) -> QuerySet[Recommendation]:
    """
    Return only pending recommendations for a trip.
    """

    return get_trip_recommendations(
        trip,
    ).filter(
        status=RecommendationStatus.PENDING,
    )


def get_accepted_recommendations(
    trip: Trip,
) -> QuerySet[Recommendation]:
    """
    Return only accepted recommendations for a trip.
    """

    return get_trip_recommendations(
        trip,
    ).filter(
        status=RecommendationStatus.ACCEPTED,
    )


def get_rejected_recommendations(
    trip: Trip,
) -> QuerySet[Recommendation]:
    """
    Return only rejected recommendations for a trip.
    """

    return get_trip_recommendations(
        trip,
    ).filter(
        status=RecommendationStatus.REJECTED,
    )