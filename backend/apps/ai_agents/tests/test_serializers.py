"""
Tests for the AI Agent serializers.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.ai_agents.models import (
    AgentRun,
    AgentRunStatus,
    AgentType,
)
from apps.ai_agents.serializers import (
    AgentRunStatusSerializer,
)
from apps.trips.models import Trip


User = get_user_model()


class AgentRunStatusSerializerTests(TestCase):
    """
    Tests for AgentRunStatusSerializer.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            email="akhil@example.com",
            password="password123",
            first_name="Akhil",
            last_name="Raj",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Tour",
            start_date=timezone.datetime(
                2026,
                9,
                10,
            ).date(),
            end_date=timezone.datetime(
                2026,
                9,
                15,
            ).date(),
            traveler_count=2,
            notes="Interested in temples.",
        )

        self.agent_run = AgentRun.objects.create(
            trip=self.trip,
            triggered_by=self.user,
            agent_type=AgentType.TRAVEL_PLANNER,
            status=AgentRunStatus.SUCCEEDED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            input_snapshot={
                "trip_title": self.trip.title,
            },
        )

    def test_serializer_contains_expected_fields(self):

        serializer = AgentRunStatusSerializer(
            self.agent_run,
        )

        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "agent_type",
                "status",
                "error_message",
                "started_at",
                "completed_at",
            },
        )

    def test_serializer_returns_correct_values(self):

        serializer = AgentRunStatusSerializer(
            self.agent_run,
        )

        data = serializer.data

        self.assertEqual(
            data["agent_type"],
            AgentType.TRAVEL_PLANNER,
        )

        self.assertEqual(
            data["status"],
            AgentRunStatus.SUCCEEDED,
        )

        self.assertEqual(
            data["error_message"],
            "",
        )

        self.assertIsNotNone(
            data["started_at"],
        )

        self.assertIsNotNone(
            data["completed_at"],
        )

    def test_serializer_is_read_only(self):

        serializer = AgentRunStatusSerializer()

        self.assertEqual(
            set(serializer.fields.keys()),
            {
                "id",
                "agent_type",
                "status",
                "error_message",
                "started_at",
                "completed_at",
            },
        )

        for field in serializer.fields.values():

            self.assertTrue(
                field.read_only,
            )