"""
REST API views for the AI Agents application.

This module exposes endpoints that allow clients to:

- Start asynchronous AI itinerary generation.
- Poll the status of an AI planning run.

The views intentionally remain lightweight.

Business logic belongs in:
- apps.ai_agents.services
- apps.ai_agents.tasks

AI execution happens asynchronously through Celery.
"""

from __future__ import annotations

from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_agents.models import AgentRun
from apps.ai_agents.serializers import (
    AgentRunStatusSerializer,
)
from apps.ai_agents.tasks import (
    run_travel_planner_task,
)
from apps.trips.models import Trip


class TripPlanView(APIView):
    """
    Queue AI itinerary generation for a trip.

    Returns immediately while the AI planning executes
    asynchronously via Celery.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        trip_id,
    ):
        """
        Queue a Travel Planner execution.
        """

        trip = get_object_or_404(
            Trip,
            pk=trip_id,
            user=request.user,
        )

        async_result = run_travel_planner_task.delay(
            trip_id=str(trip.id),
            user_id=request.user.id,
        )

        return Response(
            {
                "message": (
                    "Travel planning has been queued."
                ),
                "task_id": async_result.id,
                "trip_id": str(trip.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class TripPlanStatusView(APIView):
    """
    Retrieve the latest AI planning status for a trip.
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        trip_id,
    ):
        """
        Return the latest AgentRun for the trip.
        """

        trip = get_object_or_404(
            Trip,
            pk=trip_id,
            user=request.user,
        )

        agent_run = (
            AgentRun.objects
            .filter(
                trip=trip,
            )
            .order_by(
                "-created_at",
            )
            .first()
        )

        if agent_run is None:
            return Response(
                {
                    "detail": (
                        "No AI planning has been started "
                        "for this trip."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AgentRunStatusSerializer(
            agent_run,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )