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
    BudgetEstimateSchema,
    BudgetLineItemEstimateSchema,
    DailyWeatherSchema,
    WeatherForecastSchema,
    RecommendationBatchSchema,
    RecommendationItemSchema,
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
    _persist_budget_estimate,
    _persist_weather_forecast,
    _persist_recommendations,
)

from apps.destinations.models import Destination

from apps.budget.models import (
    Budget,
    BudgetLineItem,
)

from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)

from apps.recommendations.models import (
    Recommendation,
    RecommendationStatus,
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
        
class PersistBudgetEstimateTests(
    BaseServiceTestCase,
):
    """
    Verify persistence of AI-generated budget estimates.
    """

    def setUp(self):
        super().setUp()

        self.budget_estimate = BudgetEstimateSchema(
            line_items=[
                BudgetLineItemEstimateSchema(
                    category="food",
                    description="Meals",
                    estimated_amount=150.00,
                ),
                BudgetLineItemEstimateSchema(
                    category="transport",
                    description="Metro",
                    estimated_amount=80.00,
                ),
            ]
        )

    @patch(
        "apps.ai_agents.services.budget_services.create_budget_line_item",
    )
    def test_persist_budget_estimate(
        self,
        mock_create,
    ):
        _persist_budget_estimate(
            trip=self.trip,
            budget_estimate=self.budget_estimate,
        )

        self.assertEqual(
            Budget.objects.count(),
            1,
        )

        self.assertEqual(
            mock_create.call_count,
            2,
        )

class PersistExistingBudgetTests(
    BaseServiceTestCase,
):
    """
    Existing AI-generated budget items should be replaced,
    while manual items remain.
    """

    def setUp(self):
        super().setUp()

        self.budget, created = Budget.objects.get_or_create(
            trip=self.trip,
        )

        BudgetLineItem.objects.create(
            budget=self.budget,
            category="food",
            description="Old AI Item",
            amount=Decimal("100.00"),
            is_ai_estimated=True,
        )

        BudgetLineItem.objects.create(
            budget=self.budget,
            category="food",
            description="Manual Item",
            amount=Decimal("50.00"),
            is_ai_estimated=False,
        )

        self.estimate = BudgetEstimateSchema(
            line_items=[
                BudgetLineItemEstimateSchema(
                    category="food",
                    description="Meals",
                    estimated_amount=200.00,
                )
            ]
        )

    @patch(
        "apps.ai_agents.services.budget_services.create_budget_line_item",
    )
    def test_existing_ai_items_are_replaced(
        self,
        mock_create,
    ):
        _persist_budget_estimate(
            trip=self.trip,
            budget_estimate=self.estimate,
        )

        self.assertEqual(
            BudgetLineItem.objects.filter(
                is_ai_estimated=True,
            ).count(),
            0,
        )

        self.assertEqual(
            BudgetLineItem.objects.filter(
                is_ai_estimated=False,
            ).count(),
            1,
        )

        mock_create.assert_called_once()
        
class RunTravelPlannerBudgetPersistenceTests(
    BaseServiceTestCase,
):
    """
    Verify that successful planning persists
    both itinerary and budget.
    """

    @patch(
        "apps.ai_agents.services._persist_budget_estimate",
    )
    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    def test_budget_is_persisted(
        self,
        mock_graph,
        mock_itinerary,
        mock_budget,
    ):
        budget = BudgetEstimateSchema(
            line_items=[
                BudgetLineItemEstimateSchema(
                    category="food",
                    description="Meals",
                    estimated_amount=100.00,
                )
            ]
        )

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": ["Kyoto"],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
            "budget_estimate": budget,
        }

        run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        mock_itinerary.assert_called_once()

        mock_budget.assert_called_once()

class PersistWeatherForecastTests(
    BaseServiceTestCase,
):
    """
    Verify persistence of AI-generated weather forecasts.
    """

    def setUp(self):
        super().setUp()

        ItineraryDay.objects.create(
            trip=self.trip,
            day_number=1,
            date=date(2026, 9, 10),
            summary="Arrival",
        )

        self.forecast = WeatherForecastSchema(
            days=[
                DailyWeatherSchema(
                    date="2026-09-10",
                    condition="Sunny",
                    high_f=84,
                    low_f=72,
                    precipitation_chance=10,
                )
            ]
        )

    def test_persist_weather_forecast(self):

        _persist_weather_forecast(
            trip=self.trip,
            weather_forecast=self.forecast,
        )

        day = ItineraryDay.objects.get()

        self.assertEqual(
            day.weather_condition,
            "Sunny",
        )

        self.assertEqual(
            day.weather_high_f,
            84,
        )

        self.assertEqual(
            day.weather_low_f,
            72,
        )

        self.assertEqual(
            day.weather_precipitation_chance,
            10,
        )
        
class RunTravelPlannerWeatherPersistenceTests(
    BaseServiceTestCase,
):
    """
    Verify successful planning persists
    itinerary, budget and weather.
    """

    @patch(
        "apps.ai_agents.services._persist_weather_forecast",
    )
    @patch(
        "apps.ai_agents.services._persist_budget_estimate",
    )
    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    def test_weather_is_persisted(
        self,
        mock_graph,
        mock_itinerary,
        mock_budget,
        mock_weather,
    ):

        budget = BudgetEstimateSchema(
            line_items=[
                BudgetLineItemEstimateSchema(
                    category="food",
                    description="Meals",
                    estimated_amount=100.0,
                )
            ]
        )

        weather = WeatherForecastSchema(
            days=[
                DailyWeatherSchema(
                    date="2026-09-10",
                    condition="Sunny",
                    high_f=84,
                    low_f=72,
                    precipitation_chance=10,
                )
            ]
        )

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": ["Kyoto"],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
            "budget_estimate": budget,
            "weather_forecast": weather,
        }

        run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        mock_itinerary.assert_called_once()

        mock_budget.assert_called_once()

        mock_weather.assert_called_once()
        
class PersistRecommendationTests(
    BaseServiceTestCase,
):
    """
    Verify persistence of AI-generated recommendations.
    """

    def setUp(self):
        super().setUp()

        from ai.agents.schemas import (
            RecommendationBatchSchema,
            RecommendationItemSchema,
        )

        from apps.recommendations.models import (
            Recommendation,
            RecommendationStatus,
        )

        self.Recommendation = Recommendation
        self.RecommendationStatus = RecommendationStatus

        self.recommendations = RecommendationBatchSchema(
            recommendations=[
                RecommendationItemSchema(
                    destination="Kyoto",
                    category="attraction",
                    score=0.95,
                    reason="Visit Fushimi Inari early in the morning.",
                )
            ]
        )

    def test_existing_pending_ai_recommendations_are_replaced(
        self,
    ):
        """
        Pending AI recommendations should be replaced while accepted and
        rejected recommendations remain.
        """

        self.Recommendation.objects.create(
            trip=self.trip,
            destination=self.destination,
            category="attraction",
            score=0.50,
            reason="Old AI recommendation",
            status=self.RecommendationStatus.PENDING,
            is_ai_generated=True,
        )

        self.Recommendation.objects.create(
            trip=self.trip,
            destination=self.destination,
            category="attraction",
            score=0.80,
            reason="Accepted recommendation",
            status=self.RecommendationStatus.ACCEPTED,
            is_ai_generated=True,
        )

        self.Recommendation.objects.create(
            trip=self.trip,
            destination=self.destination,
            category="attraction",
            score=0.20,
            reason="Rejected recommendation",
            status=self.RecommendationStatus.REJECTED,
            is_ai_generated=True,
        )

        _persist_recommendations(
            trip=self.trip,
            recommendations=self.recommendations,
        )

        self.assertEqual(
            self.Recommendation.objects.filter(
                status=self.RecommendationStatus.PENDING,
            ).count(),
            1,
        )

        self.assertEqual(
            self.Recommendation.objects.filter(
                status=self.RecommendationStatus.ACCEPTED,
            ).count(),
            1,
        )

        self.assertEqual(
            self.Recommendation.objects.filter(
                status=self.RecommendationStatus.REJECTED,
            ).count(),
            1,
        )

        new_recommendation = self.Recommendation.objects.get(
            status=self.RecommendationStatus.PENDING,
        )

        self.assertEqual(
            new_recommendation.reason,
            "Visit Fushimi Inari early in the morning.",
        )

        self.assertTrue(
            new_recommendation.is_ai_generated,
        )
        
class RunTravelPlannerRecommendationPersistenceTests(
    BaseServiceTestCase,
):
    """
    Verify successful planning persists itinerary, budget, weather
    and recommendations.
    """

    @patch(
        "apps.ai_agents.services._persist_recommendations",
    )
    @patch(
        "apps.ai_agents.services._persist_weather_forecast",
    )
    @patch(
        "apps.ai_agents.services._persist_budget_estimate",
    )
    @patch(
        "apps.ai_agents.services._persist_itinerary_plan",
    )
    @patch(
        "apps.ai_agents.services.run_planning_graph",
    )
    def test_recommendations_are_persisted(
        self,
        mock_graph,
        mock_itinerary,
        mock_budget,
        mock_weather,
        mock_recommendations,
    ):
        budget = BudgetEstimateSchema(
            line_items=[
                BudgetLineItemEstimateSchema(
                    category="food",
                    description="Meals",
                    estimated_amount=100.00,
                )
            ]
        )

        weather = WeatherForecastSchema(
            days=[
                DailyWeatherSchema(
                    date="2026-09-10",
                    condition="Sunny",
                    high_f=84,
                    low_f=72,
                    precipitation_chance=10,
                )
            ]
        )

        recommendations = RecommendationBatchSchema(
            recommendations=[
                RecommendationItemSchema(
                    destination="Kyoto",
                    category="attraction",
                    score=0.95,
                    reason="Visit Fushimi Inari Shrine.",
                )
            ]
        )

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": ["Kyoto"],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
            "budget_estimate": budget,
            "weather_forecast": weather,
            "recommendations": recommendations,
        }

        run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        mock_itinerary.assert_called_once()

        mock_budget.assert_called_once()

        mock_weather.assert_called_once()

        mock_recommendations.assert_called_once()