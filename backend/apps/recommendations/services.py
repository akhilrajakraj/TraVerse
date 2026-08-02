"""
Business services for the Recommendations application.
"""

from apps.recommendations.models import (
    Recommendation,
    RecommendationStatus,
)


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