"""
Tests for the AI service layer.

These tests verify the only Django entry point into the AI package.

Covered:

- _build_initial_state()
- _persist_itinerary_plan()
- run_travel_planner()
- AgentRun lifecycle
- Failure handling
- Review handling
"""

from __future__ import annotations

from datetime import date
from datetime import time
from decimal import Decimal
from unittest.mock import MagicMock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ai.exceptions import (
    LLMCallFailed,
    StructuredOutputInvalid,
)

from ai.agents.schemas import (
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
)

from apps.ai_agents.models import (
    AgentRun,
    AgentRunStatus,
    AgentType,
)

from apps.ai_agents.services import (
    _build_initial_state,
    _persist_itinerary_plan,
    run_travel_planner,
)

from apps.destinations.models import Destination

from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)

from apps.trips.models import Trip


User = get_user_model()


class BaseServiceTestCase(TestCase):
    """
    Common fixtures shared across AI service tests.
    """

    def setUp(self):

        self.user = User.objects.create_user(
            email="akhil@example.com",
            password="password123",
            first_name="Akhil",
            last_name="Raj",
        )

        self.destination = Destination.objects.create(
            name="Kyoto",
            country="Japan",
            city="Kyoto",
            latitude=Decimal("35.011600"),
            longitude=Decimal("135.768100"),
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Tour",
            start_date=date(
                2026,
                9,
                10,
            ),
            end_date=date(
                2026,
                9,
                15,
            ),
            traveler_count=2,
            notes="Interested in temples and local cuisine.",
        )

        self.trip.destinations.add(
            self.destination,
        )

        self.plan = ItineraryPlanSchema(
            days=[
                ItineraryDaySchema(
                    day_number=1,
                    date=date(
                        2026,
                        9,
                        10,
                    ),
                    summary="Arrival",
                    items=[
                        ItineraryItemSchema(
                            title="Hotel Check-in",
                            description="Check into hotel.",
                            start_time=time(
                                14,
                                0,
                            ),
                            estimated_cost_usd=Decimal(
                                "120.00",
                            ),
                        )
                    ],
                )
            ]
        )


class BuildInitialStateTests(
    BaseServiceTestCase,
):

    def test_build_initial_state(self):

        state = _build_initial_state(
            self.trip,
        )

        self.assertEqual(
            state["trip_title"],
            "Japan Tour",
        )

        self.assertEqual(
            state["destination_names"],
            [
                "Kyoto",
            ],
        )

        self.assertEqual(
            state["traveler_count"],
            2,
        )

        self.assertEqual(
            state["trip_notes"],
            "Interested in temples and local cuisine.",
        )

        self.assertEqual(
            state["start_date"],
            "2026-09-10",
        )

        self.assertEqual(
            state["end_date"],
            "2026-09-15",
        )


class PersistItineraryTests(
    BaseServiceTestCase,
):

    @patch(
        "apps.ai_agents.services.itinerary_services.add_item_to_day",
    )
    def test_persist_itinerary_plan(
        self,
        mock_add_item,
    ):

        _persist_itinerary_plan(
            trip=self.trip,
            plan=self.plan,
        )

        self.assertEqual(
            ItineraryDay.objects.count(),
            1,
        )

        day = ItineraryDay.objects.get()

        self.assertEqual(
            day.day_number,
            1,
        )

        self.assertEqual(
            day.summary,
            "Arrival",
        )

        mock_add_item.assert_called_once()


class RunTravelPlannerSuccessTests(
    BaseServiceTestCase,
):

    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    def test_run_travel_planner_success(
        self,
        mock_graph,
        mock_persist,
    ):

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": [
                "Kyoto",
            ],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
        }

        agent_run = run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        self.assertEqual(
            agent_run.status,
            AgentRunStatus.SUCCEEDED,
        )

        self.assertEqual(
            agent_run.agent_type,
            AgentType.TRAVEL_PLANNER,
        )

        mock_graph.assert_called_once()

        mock_persist.assert_called_once()

class RunTravelPlannerFailureTests(
    BaseServiceTestCase,
):
    """
    Verify failures originating from the AI layer.
    """

    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    def test_llm_failure_marks_agent_run_failed(
        self,
        mock_persist,
        mock_graph,
    ):
        """
        If the LLM provider fails, the AgentRun should be
        marked as FAILED and no itinerary should be persisted.
        """

        mock_graph.side_effect = LLMCallFailed(
            "Groq API unavailable",
        )

        agent_run = run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        agent_run.refresh_from_db()

        self.assertEqual(
            agent_run.status,
            AgentRunStatus.FAILED,
        )

        self.assertEqual(
            agent_run.agent_type,
            AgentType.TRAVEL_PLANNER,
        )

        self.assertEqual(
            agent_run.error_message,
            "Groq API unavailable",
        )

        self.assertIsNotNone(
            agent_run.completed_at,
        )

        mock_graph.assert_called_once()

        mock_persist.assert_not_called()


class RunTravelPlannerNeedsReviewTests(
    BaseServiceTestCase,
):
    """
    Verify handling of invalid structured output.
    """

    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    def test_invalid_output_marks_agent_for_review(
        self,
        mock_persist,
        mock_graph,
    ):

        mock_graph.side_effect = StructuredOutputInvalid(
            "Invalid itinerary schema",
        )

        agent_run = run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        agent_run.refresh_from_db()

        self.assertEqual(
            agent_run.status,
            AgentRunStatus.NEEDS_REVIEW,
        )

        self.assertEqual(
            agent_run.error_message,
            "Invalid itinerary schema",
        )

        self.assertIsNotNone(
            agent_run.completed_at,
        )

        mock_graph.assert_called_once()

        mock_persist.assert_not_called()


class PersistExistingItineraryTests(
    BaseServiceTestCase,
):
    """
    Existing AI itinerary should be replaced.
    """

    @patch(
        "apps.ai_agents.services.itinerary_services.add_item_to_day",
    )
    def test_existing_items_are_replaced(
        self,
        mock_add_item,
    ):

        day = ItineraryDay.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(
                2026,
                9,
                10,
            ),
            summary="Old Summary",
        )

        ItineraryItem.objects.create(
            day=day,
            title="Old Item",
            description="Old",
            is_ai_generated=True,
        )

        self.assertEqual(
            ItineraryItem.objects.count(),
            1,
        )

        _persist_itinerary_plan(
            trip=self.trip,
            plan=self.plan,
        )

        #
        # Old AI item should have been deleted.
        #
        self.assertEqual(
            ItineraryItem.objects.count(),
            0,
        )

        mock_add_item.assert_called_once()


class AgentRunCreationTests(
    BaseServiceTestCase,
):
    """
    Verify AgentRun metadata.
    """

    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    def test_input_snapshot_saved(
        self,
        mock_graph,
        mock_persist,
    ):

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": [
                "Kyoto",
            ],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
        }

        agent_run = run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        snapshot = agent_run.input_snapshot

        self.assertEqual(
            snapshot["trip_title"],
            self.trip.title,
        )

        self.assertEqual(
            snapshot["traveler_count"],
            2,
        )

        self.assertEqual(
            snapshot["trip_notes"],
            self.trip.notes,
        )

        self.assertEqual(
            snapshot["destination_names"],
            [
                "Kyoto",
            ],
        )

        self.assertEqual(
            snapshot["start_date"],
            "2026-09-10",
        )

        self.assertEqual(
            snapshot["end_date"],
            "2026-09-15",
        )

        mock_graph.assert_called_once()

        mock_persist.assert_called_once()