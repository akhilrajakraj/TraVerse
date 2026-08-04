"""
Tests for the AI Agent REST API views.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_agents.models import (
    AgentRun,
    AgentRunStatus,
    AgentType,
)

from apps.destinations.models import Destination
from apps.trips.models import Trip


User = get_user_model()


class BaseViewTestCase(APITestCase):
    """
    Common fixtures shared across view tests.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            email="akhil@example.com",
            password="password123",
            first_name="Akhil",
            last_name="Raj",
        )

        self.client.force_authenticate(
            self.user,
        )

        self.destination = Destination.objects.create(
            name="Kyoto",
            city="Kyoto",
            country="Japan",
            latitude=35.0116,
            longitude=135.7681,
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Tour",
            start_date="2026-09-10",
            end_date="2026-09-15",
            traveler_count=2,
            notes="Temples and food",
        )

        self.trip.destinations.add(
            self.destination,
        )


class TripPlanViewTests(BaseViewTestCase):

    @patch(
        "apps.ai_agents.views.run_travel_planner_task.delay",
    )
    def test_queue_travel_plan(
        self,
        mock_delay,
    ):

        mock_result = MagicMock()
        mock_result.id = "celery-task-id"

        mock_delay.return_value = mock_result

        response = self.client.post(
            reverse(
                "ai_agents:trip-plan",
                kwargs={
                    "trip_id": self.trip.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
        )

        self.assertEqual(
            response.data["task_id"],
            "celery-task-id",
        )

        self.assertEqual(
            response.data["trip_id"],
            str(self.trip.id),
        )

        mock_delay.assert_called_once_with(
            trip_id=str(self.trip.id),
            user_id=self.user.id,
        )


class TripPlanStatusViewTests(BaseViewTestCase):

    def test_status_returns_404_when_no_agent_run(self):

        response = self.client.get(
            reverse(
                "ai_agents:trip-plan-status",
                kwargs={
                    "trip_id": self.trip.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_status_returns_latest_agent_run(self):

        AgentRun.objects.create(
            trip=self.trip,
            triggered_by=self.user,
            agent_type=AgentType.TRAVEL_PLANNER,
            status=AgentRunStatus.RUNNING,
            input_snapshot={},
        )

        response = self.client.get(
            reverse(
                "ai_agents:trip-plan-status",
                kwargs={
                    "trip_id": self.trip.id,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["status"],
            AgentRunStatus.RUNNING,
        )

        self.assertEqual(
            response.data["agent_type"],
            AgentType.TRAVEL_PLANNER,
        )