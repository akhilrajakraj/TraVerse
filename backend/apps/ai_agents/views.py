"""REST API views for asynchronous AI planning."""

from __future__ import annotations

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_agents.models import AgentRun
from apps.ai_agents.serializers import AgentRunStatusSerializer
from apps.ai_agents.tasks import run_travel_planner_task
from apps.core.rate_limiting import increment_rate_limit, is_rate_limited
from apps.trips.models import Trip


_PLAN_RATE_LIMIT_MAX = 5
_PLAN_RATE_LIMIT_WINDOW_SECONDS = 3600


class TripPlanView(APIView):
    """Queue AI itinerary generation for a trip."""

    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

        rate_limit_key = f"plan_trigger_rate_limit:{request.user.id}"
        if is_rate_limited(
            key=rate_limit_key,
            max_requests=_PLAN_RATE_LIMIT_MAX,
        ):
            return Response(
                {
                    "error": {
                        "code": "rate_limited",
                        "message": (
                            f"Maximum {_PLAN_RATE_LIMIT_MAX} planning requests per hour."
                        ),
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        increment_rate_limit(
            key=rate_limit_key,
            window_seconds=_PLAN_RATE_LIMIT_WINDOW_SECONDS,
        )

        async_result = run_travel_planner_task.delay(
            trip_id=str(trip.id),
            user_id=request.user.id,
        )

        return Response(
            {
                "message": "Travel planning has been queued.",
                "task_id": async_result.id,
                "trip_id": str(trip.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TripPlanStatusView(APIView):
    """Retrieve the latest AI planning status for a trip."""

    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

        agent_run = (
            AgentRun.objects.filter(trip=trip).order_by("-created_at").first()
        )

        if agent_run is None:
            return Response(
                {"detail": "No AI planning has been started for this trip."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            AgentRunStatusSerializer(agent_run).data,
            status=status.HTTP_200_OK,
        )
