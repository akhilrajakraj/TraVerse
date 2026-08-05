"""
Business services for the Recommendations application.
"""

from decimal import Decimal

from apps.recommendations.models import (
    Recommendation,
    RecommendationStatus,
    RecommendationCategory,
)

from apps.destinations.models import Destination

from apps.trips.models import Trip


def accept_recommendation(
    recommendation: Recommendation,
) -> Recommendation:
    """
    Mark a recommendation as accepted.
    """

    recommendation.status = RecommendationStatus.ACCEPTED

    recommendation.save(
        update_fields=[
            "status",
        ],
    )

    return recommendation


def reject_recommendation(
    recommendation: Recommendation,
) -> Recommendation:
    """
    Mark a recommendation as rejected.
    """

    recommendation.status = RecommendationStatus.REJECTED

    recommendation.save(
        update_fields=[
            "status",
        ],
    )

    return recommendation

def create_recommendation(
    *,
    trip: Trip,
    destination: Destination,
    category: RecommendationCategory,
    score: Decimal,
    reason: str,
    is_ai_generated: bool = True,
) -> Recommendation:
    """
    Create a new recommendation.

    This is the single write entry point used by both AI-generated and
    manually created recommendations.

    Business ownership of Recommendation creation remains inside the
    Recommendations application.
    """

    return Recommendation.objects.create(
        trip=trip,
        destination=destination,
        category=category,
        score=score,
        reason=reason,
        status=RecommendationStatus.PENDING,
        is_ai_generated=is_ai_generated,
    )


def clear_pending_ai_recommendations(
    *,
    trip: Trip,
) -> int:
    """
    Remove only pending AI-generated recommendations.

    Accepted recommendations represent explicit user decisions and must
    never be removed automatically.

    Rejected recommendations are preserved as user feedback and may be
    valuable for future recommendation strategies.

    Returns:
        Number of deleted recommendations.
    """

    deleted_count, _ = Recommendation.objects.filter(
        trip=trip,
        is_ai_generated=True,
        status=RecommendationStatus.PENDING,
    ).delete()

    return deleted_count