"""Chapter 27-compatible AI service tests.

The Chapter 27 performance refactor changed several private service contracts from
per-row helpers to batch-oriented operations.  The original service tests were
written against the old call shape, so this module preserves their coverage while
updating only the affected expectations to the production contracts.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.ai_agents.services import (
    _attach_conversation_context,
    _persist_budget_estimate,
    _persist_itinerary_plan,
    _persist_weather_forecast,
    run_travel_planner,
)
from apps.budget.models import BudgetLineItem
from apps.itinerary.models import ItineraryDay, ItineraryItem
from apps.notifications.models import NotificationType

from . import services_legacy as legacy


_REPLACED_CLASSES = {
    "PersistItineraryTests",
    "RunTravelPlannerSuccessTests",
    "PersistExistingItineraryTests",
    "PersistBudgetEstimateTests",
    "PersistExistingBudgetTests",
    "PersistWeatherForecastTests",
    "AttachConversationContextTests",
}

# Preserve every unaffected test case from the pre-refactor module.  The legacy
# module is intentionally not named test*.py, so unittest discovery sees these
# classes only through this compatibility module.
for _name, _obj in vars(legacy).items():
    if (
        _name not in _REPLACED_CLASSES
        and isinstance(_obj, type)
        and issubclass(_obj, TestCase)
    ):
        globals()[_name] = _obj


class PersistItineraryTests(legacy.PersistItineraryTests):
    """Verify the batch itinerary persistence contract."""

    def test_persist_itinerary_plan(self):
        itinerary_days = _persist_itinerary_plan(
            trip=self.trip,
            plan=self.plan,
        )

        self.assertEqual(ItineraryDay.objects.count(), 1)
        day = ItineraryDay.objects.get()

        self.assertEqual(day.day_number, 1)
        self.assertEqual(day.summary, "Arrival")
        self.assertEqual(itinerary_days[date(2026, 9, 10)], day)

        item = ItineraryItem.objects.get()
        self.assertEqual(item.title, "Hotel Check-in")
        self.assertEqual(item.order, 10)
        self.assertTrue(item.is_ai_generated)


class RunTravelPlannerSuccessTests(legacy.RunTravelPlannerSuccessTests):
    """Verify successful planning against the refactored notification import."""

    @patch("apps.ai_agents.services.create_notification")
    @patch("apps.ai_agents.services._persist_itinerary_plan")
    @patch("apps.ai_agents.services.run_planning_graph")
    def test_run_travel_planner_success(
        self,
        mock_graph,
        mock_persist,
        mock_create_notification,
    ):
        mock_persist.return_value = {}
        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": ["Kyoto"],
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

        self.assertEqual(agent_run.status, "succeeded")
        self.assertEqual(agent_run.agent_type, "travel_planner")
        mock_graph.assert_called_once()
        mock_persist.assert_called_once_with(
            trip=self.trip,
            plan=self.plan,
        )
        mock_create_notification.assert_called_once_with(
            user=self.trip.user,
            notification_type=NotificationType.TRIP_PLAN_READY,
            subject="Your itinerary for Japan Tour is ready!",
            body=(
                "Your AI-generated plan for Japan Tour "
                "(2026-09-10 to 2026-09-15) is ready to view."
            ),
        )


class PersistExistingItineraryTests(legacy.PersistExistingItineraryTests):
    """Verify replacement through the batch itinerary writer."""

    def test_existing_items_are_replaced(self):
        day = ItineraryDay.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 9, 10),
            summary="Old Summary",
        )
        ItineraryItem.objects.create(
            day=day,
            title="Old Item",
            description="Old",
            is_ai_generated=True,
        )

        _persist_itinerary_plan(
            trip=self.trip,
            plan=self.plan,
        )

        self.assertEqual(ItineraryItem.objects.count(), 1)
        replacement = ItineraryItem.objects.get()
        self.assertEqual(replacement.title, "Hotel Check-in")
        self.assertTrue(replacement.is_ai_generated)


class PersistBudgetEstimateTests(legacy.PersistBudgetEstimateTests):
    """Verify batch budget replacement rather than per-item service calls."""

    def test_persist_budget_estimate(self):
        _persist_budget_estimate(
            trip=self.trip,
            budget_estimate=self.budget_estimate,
        )

        items = list(
            BudgetLineItem.objects
            .filter(budget__trip=self.trip, is_ai_estimated=True)
            .order_by("description")
        )

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].amount, Decimal("150.00"))
        self.assertEqual(items[1].amount, Decimal("80.00"))
        self.assertEqual(
            {item.description for item in items},
            {"Meals", "Metro"},
        )


class PersistExistingBudgetTests(legacy.PersistExistingBudgetTests):
    """Verify only generated budget rows are replaced."""

    def test_existing_ai_items_are_replaced(self):
        _persist_budget_estimate(
            trip=self.trip,
            budget_estimate=self.estimate,
        )

        ai_items = list(
            BudgetLineItem.objects
            .filter(budget=self.budget, is_ai_estimated=True)
        )
        manual_items = list(
            BudgetLineItem.objects
            .filter(budget=self.budget, is_ai_estimated=False)
        )

        self.assertEqual(len(ai_items), 1)
        self.assertEqual(ai_items[0].description, "Meals")
        self.assertEqual(ai_items[0].amount, Decimal("200.00"))
        self.assertEqual(len(manual_items), 1)
        self.assertEqual(manual_items[0].description, "Manual Item")
        self.assertEqual(manual_items[0].amount, Decimal("50.00"))
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.computed_budget_total, Decimal("250.00"))


class PersistWeatherForecastTests(legacy.PersistWeatherForecastTests):
    """Verify weather persistence consumes the resolved day mapping."""

    def test_persist_weather_forecast(self):
        day = ItineraryDay.objects.get()

        _persist_weather_forecast(
            trip=self.trip,
            weather_forecast=self.forecast,
            itinerary_days={day.date: day},
        )

        day.refresh_from_db()
        self.assertEqual(day.weather_condition, "Sunny")
        self.assertEqual(day.weather_high_f, 84)
        self.assertEqual(day.weather_low_f, 72)
        self.assertEqual(day.weather_precipitation_chance, 10)


class AttachConversationContextTests(legacy.AttachConversationContextTests):
    """Verify the optimized session-injection contract."""

    def test_returns_original_state_when_no_session(self):
        state = {"trip_title": self.trip.title}

        result = _attach_conversation_context(
            session=None,
            state=state,
        )

        self.assertEqual(result, state)
        self.assertNotIn("conversation_context", result)

    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    def test_conversation_context_added(
        self,
        mock_build_memory,
        mock_manager,
    ):
        session = legacy.MagicMock()
        memory = legacy.MagicMock()
        memory.transcript.return_value = "Conversation Summary"
        mock_build_memory.return_value = memory

        manager = legacy.MagicMock()
        manager.optimize_memory.return_value = memory
        mock_manager.return_value = manager

        state = {"trip_title": self.trip.title}

        result = _attach_conversation_context(
            session=session,
            state=state,
        )

        mock_build_memory.assert_called_once_with(session=session)
        manager.optimize_memory.assert_called_once_with(memory)
        self.assertEqual(
            result["conversation_context"],
            "Conversation Summary",
        )
