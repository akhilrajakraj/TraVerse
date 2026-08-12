"""
Business services for the Recommendations application.

Recommendation decisions are intentionally modeled as a small state machine:
pending -> accepted/rejected, with accepted and rejected both terminal.
"""

from decimal import Decimal

from apps.destinations.models import Destination
from apps.recommendations.models import (
    Recommendation,
    RecommendationCategory,
    RecommendationStatus,
)
from apps.trips.models import Trip
from apps.core.exceptions import BusinessRuleViolation


class InvalidRecommendationTransition(BusinessRuleViolation):
    """Raised when a recommendation cannot move to the requested state."""

    default_message = (
        "This recommendation has already been decided and cannot be changed."
    )
    default_code = "invalid_recommendation_transition"


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    RecommendationStatus.PENDING: {
        RecommendationStatus.ACCEPTED,
        RecommendationStatus.REJECTED,
    },
    RecommendationStatus.ACCEPTED: set(),
    RecommendationStatus.REJECTED: set(),
}


def _transition(
    recommendation: Recommendation,
    new_status: str,
) -> Recommendation:
    allowed = _ALLOWED_TRANSITIONS.get(recommendation.status, set())

    if new_status not in allowed:
        raise InvalidRecommendationTransition()

    recommendation.status = new_status
    recommendation.save(
        update_fields=[
            "status",
            "updated_at",
        ],
    )

    return recommendation


def accept_recommendation(
    recommendation: Recommendation,
) -> Recommendation:
    """Mark a pending recommendation as accepted."""

    return _transition(
        recommendation,
        RecommendationStatus.ACCEPTED,
    )


def reject_recommendation(
    recommendation: Recommendation,
) -> Recommendation:
    """Mark a pending recommendation as rejected."""

    return _transition(
        recommendation,
        RecommendationStatus.REJECTED,
    )


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

    This remains the application-owned write entry point for future AI
    agents and any future trusted/manual producer. Users do not create
    recommendation rows directly through the current API.
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
    never be removed automatically. Rejected recommendations are retained
    as feedback for future recommendation strategies.
    """

    deleted_count, _ = Recommendation.objects.filter(
        trip=trip,
        is_ai_generated=True,
        status=RecommendationStatus.PENDING,
    ).delete()

    return deleted_count
