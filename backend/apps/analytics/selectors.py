"""
Read-only analytics selectors.

Every function in this module reads existing application tables and never
creates or mutates records. Analytics owns no database state of its own.
"""

from django.db.models import Count, Q

from apps.ai_agents.models import AgentRun, AgentRunStatus
from apps.bookings.models import Booking
from apps.recommendations.models import Recommendation, RecommendationStatus
from apps.trips.models import Trip, TripStatus


def get_platform_summary() -> dict:
    """Return platform-level trip and AI execution aggregates."""
    trip_aggregates = Trip.objects.aggregate(
        total=Count("id"),
        draft=Count("id", filter=Q(status=TripStatus.DRAFT)),
        planning=Count("id", filter=Q(status=TripStatus.PLANNING)),
        planned=Count("id", filter=Q(status=TripStatus.PLANNED)),
        completed=Count("id", filter=Q(status=TripStatus.COMPLETED)),
        cancelled=Count("id", filter=Q(status=TripStatus.CANCELLED)),
    )

    agent_aggregates = AgentRun.objects.aggregate(
        total=Count("id"),
        succeeded=Count("id", filter=Q(status=AgentRunStatus.SUCCEEDED)),
        failed=Count("id", filter=Q(status=AgentRunStatus.FAILED)),
        needs_review=Count("id", filter=Q(status=AgentRunStatus.NEEDS_REVIEW)),
    )

    total = agent_aggregates["total"]
    success_rate = (
        agent_aggregates["succeeded"] / total if total else 0.0
    )

    return {
        "total_trips": trip_aggregates["total"],
        "trips_by_status": {
            "draft": trip_aggregates["draft"],
            "planning": trip_aggregates["planning"],
            "planned": trip_aggregates["planned"],
            "completed": trip_aggregates["completed"],
            "cancelled": trip_aggregates["cancelled"],
        },
        "total_agent_runs": total,
        "agent_success_rate": round(success_rate, 2),
    }


def get_agent_performance_summary() -> dict:
    """Return aggregate counts for AI execution outcomes in one query."""
    return AgentRun.objects.aggregate(
        total=Count("id"),
        succeeded=Count("id", filter=Q(status=AgentRunStatus.SUCCEEDED)),
        failed=Count("id", filter=Q(status=AgentRunStatus.FAILED)),
        needs_review=Count("id", filter=Q(status=AgentRunStatus.NEEDS_REVIEW)),
        pending_or_running=Count(
            "id",
            filter=Q(
                status__in=[AgentRunStatus.PENDING, AgentRunStatus.RUNNING]
            ),
        ),
    )


def get_recommendation_acceptance_rate() -> float:
    """Return the accepted/decided recommendation ratio, excluding pending."""
    aggregates = (
        Recommendation.objects
        .exclude(status=RecommendationStatus.PENDING)
        .aggregate(
            total_decided=Count("id"),
            accepted=Count(
                "id",
                filter=Q(status=RecommendationStatus.ACCEPTED),
            ),
        )
    )

    if aggregates["total_decided"] == 0:
        return 0.0

    return round(aggregates["accepted"] / aggregates["total_decided"], 2)


def get_booking_intent_summary() -> dict:
    """Return aggregate counts for booking intents in one query."""
    return Booking.objects.aggregate(
        total=Count("id"),
        from_recommendation=Count(
            "id",
            filter=Q(source_recommendation__isnull=False),
        ),
        flights=Count("id", filter=Q(booking_type="flight")),
        hotels=Count("id", filter=Q(booking_type="hotel")),
        activities=Count("id", filter=Q(booking_type="activity")),
    )
