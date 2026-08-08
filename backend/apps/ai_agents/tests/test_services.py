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
from unittest.mock import patch, ANY

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
    PackingItemSchema,
    PackingListSchema,
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
    _persist_packing_list,
    generate_chat_reply,
)

from apps.destinations.models import Destination

from apps.trips.models import Trip

from apps.trips.models import (
    Trip,
    PackingItem,
    PackingCategory,
)

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
    
class PersistPackingListTests(
    BaseServiceTestCase,
):
    """
    Verify persistence of AI-generated packing items.
    """

    def setUp(self):
        super().setUp()

        self.packing_list = PackingListSchema(
            items=[
                PackingItemSchema(
                    category="clothing",
                    item="Rain Jacket",
                    quantity=1,
                    reason="Expected rain.",
                ),
                PackingItemSchema(
                    category="documents",
                    item="Passport",
                    quantity=1,
                    reason="International travel.",
                ),
            ]
        )

    def test_existing_ai_packing_items_are_replaced(
        self,
    ):
        """
        Existing AI-generated packing items should be replaced
        while manual packing items remain.
        """

        PackingItem.objects.create(
            trip=self.trip,
            category=PackingCategory.CLOTHING,
            item="Old Jacket",
            quantity=1,
            reason="Old AI item",
            is_ai_generated=True,
        )

        PackingItem.objects.create(
            trip=self.trip,
            category=PackingCategory.CLOTHING,
            item="Manual Backpack",
            quantity=1,
            reason="User item",
            is_ai_generated=False,
        )

        _persist_packing_list(
            trip=self.trip,
            packing_list=self.packing_list,
        )

        self.assertEqual(
            PackingItem.objects.filter(
                is_ai_generated=True,
            ).count(),
            2,
        )

        self.assertEqual(
            PackingItem.objects.filter(
                is_ai_generated=False,
            ).count(),
            1,
        )

        jacket = PackingItem.objects.get(
            item="Rain Jacket",
        )

        self.assertEqual(
            jacket.category,
            PackingCategory.CLOTHING,
        )

        self.assertEqual(
            jacket.quantity,
            1,
        )

        self.assertEqual(
            jacket.reason,
            "Expected rain.",
        )

class RunTravelPlannerPackingPersistenceTests(
    BaseServiceTestCase,
):
    """
    Verify successful planning persists packing items.
    """

    @patch(
        "apps.ai_agents.services._persist_packing_list",
    )
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
    def test_packing_list_is_persisted(
        self,
        mock_graph,
        mock_itinerary,
        mock_budget,
        mock_weather,
        mock_recommendations,
        mock_packing,
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

        packing = PackingListSchema(
            items=[
                PackingItemSchema(
                    category="clothing",
                    item="Rain Jacket",
                    quantity=1,
                    reason="Expected rain.",
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
            "packing_list": packing,
        }

        run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        mock_itinerary.assert_called_once()
        mock_budget.assert_called_once()
        mock_weather.assert_called_once()
        mock_recommendations.assert_called_once()
        mock_packing.assert_called_once()
        
class AttachConversationContextTests(BaseServiceTestCase):
    """
    Tests for attaching persisted chat history to the planning graph.
    """

    @patch("apps.ai_agents.services.ChatService.get_active_session")
    def test_returns_original_state_when_no_session(
        self,
        mock_get_session,
    ):
        from apps.ai_agents.services import (
            _attach_conversation_context,
        )

        mock_get_session.return_value = None

        state = {
            "trip_title": self.trip.title,
        }

        result = _attach_conversation_context(
            trip=self.trip,
            state=state,
        )

        self.assertEqual(result, state)
        self.assertNotIn("conversation_context", result)

    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    @patch("apps.ai_agents.services.ChatService.get_active_session")
    def test_conversation_context_added(
        self,
        mock_get_session,
        mock_build_memory,
        mock_manager,
    ):
        from apps.ai_agents.services import (
            _attach_conversation_context,
        )

        session = MagicMock()
        memory = MagicMock()

        memory.transcript.return_value = (
            "Conversation Summary"
        )

        mock_get_session.return_value = session

        mock_build_memory.return_value = memory

        manager = MagicMock()

        manager.optimize_memory.return_value = memory

        mock_manager.return_value = manager

        state = {
            "trip_title": self.trip.title,
        }

        result = _attach_conversation_context(
            trip=self.trip,
            state=state,
        )

        mock_build_memory.assert_called_once_with(
            session=session,
        )

        manager.optimize_memory.assert_called_once_with(
            memory,
        )

        self.assertEqual(
            result["conversation_context"],
            "Conversation Summary",
        )
        
class AttachDestinationContextTests(BaseServiceTestCase):
    """
    Tests for destination retrieval context.
    """

    def test_returns_original_state(self):
        from apps.ai_agents.services import (
            _attach_destination_context,
        )

        state = {
            "trip_title": self.trip.title,
        }

        result = _attach_destination_context(
            state=state,
            user_message="Tokyo",
        )

        self.assertEqual(
            result,
            state,
        )
        

class RunTravelPlannerConversationTests(BaseServiceTestCase):
    """
    Verify assistant responses are persisted.
    """

    @patch("apps.ai_agents.services.ChatService.add_assistant_message")
    @patch("apps.ai_agents.services.ChatService.get_active_session")
    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    @patch("apps.ai_agents.services._persist_itinerary_plan")
    @patch("apps.ai_agents.services.run_planning_graph")
    def test_assistant_response_saved(
        self,
        mock_graph,
        mock_persist,
        mock_build_memory,
        mock_manager,
        mock_get_session,
        mock_add_message,
    ):
        session = MagicMock()

        mock_get_session.return_value = session

        memory = MagicMock()

        memory.transcript.return_value = "history"

        mock_build_memory.return_value = memory

        manager = MagicMock()

        manager.optimize_memory.return_value = memory

        mock_manager.return_value = manager

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": ["Kyoto"],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
            "assistant_response": "Here is your itinerary.",
        }

        run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        mock_add_message.assert_called_once_with(
            session=session,
            content="Here is your itinerary.",
        )

    @patch("apps.ai_agents.services.ChatService.add_assistant_message")
    @patch("apps.ai_agents.services.ChatService.get_active_session")
    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    @patch("apps.ai_agents.services._persist_itinerary_plan")
    @patch("apps.ai_agents.services.run_planning_graph")
    def test_missing_assistant_response_ignored(
        self,
        mock_graph,
        mock_persist,
        mock_build_memory,
        mock_manager,
        mock_get_session,
        mock_add_message,
    ):
        session = MagicMock()

        mock_get_session.return_value = session

        memory = MagicMock()

        memory.transcript.return_value = "history"

        mock_build_memory.return_value = memory

        manager = MagicMock()

        manager.optimize_memory.return_value = memory

        mock_manager.return_value = manager

        mock_graph.return_value = {
            "trip_title": self.trip.title,
            "destination_names": ["Kyoto"],
            "start_date": "2026-09-10",
            "end_date": "2026-09-15",
            "traveler_count": 2,
            "trip_notes": self.trip.notes,
            "itinerary": self.plan,
        }

        run_travel_planner(
            trip=self.trip,
            triggered_by=self.user,
        )

        mock_add_message.assert_not_called()
        
class GenerateChatReplyTests(BaseServiceTestCase):
    """
    Verify the conversational AI entry point.
    """

    @patch("apps.ai_agents.services.ChatAgent")
    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    @patch("apps.ai_agents.services.ChatService")
    def test_generate_chat_reply(
        self,
        mock_chat_service,
        mock_build_memory,
        mock_manager,
        mock_chat_agent,
    ):
        """
        User message should be persisted, conversation optimized,
        assistant invoked and assistant reply persisted.
        """

        from apps.ai_agents.services import generate_chat_reply

        session = MagicMock()
        memory = MagicMock()

        memory.transcript.return_value = "Conversation History"

        mock_chat_service.get_or_create_active_session.return_value = session

        mock_build_memory.return_value = memory

        manager = MagicMock()
        manager.optimize_memory.return_value = memory
        mock_manager.return_value = manager

        agent = MagicMock()
        agent.reply.return_value = "Welcome to Japan!"
        mock_chat_agent.return_value = agent

        response = generate_chat_reply(
            trip=self.trip,
            user_message="Plan my trip.",
        )

        mock_chat_service.get_or_create_active_session.assert_called_once_with(
            trip=self.trip,
        )

        mock_chat_service.add_user_message.assert_called_once_with(
            session=session,
            content="Plan my trip.",
        )

        mock_build_memory.assert_called_once_with(
            session=session,
        )

        manager.optimize_memory.assert_called_once_with(
            memory,
        )

        agent.reply.assert_called_once()

        mock_chat_service.add_assistant_message.assert_called_once_with(
            session=session,
            content="Welcome to Japan!",
        )

        self.assertEqual(
            response,
            "Welcome to Japan!",
        )

    @patch("apps.ai_agents.services.ChatAgent")
    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    @patch("apps.ai_agents.services.ChatService")
    def test_generate_chat_reply_without_history(
        self,
        mock_chat_service,
        mock_build_memory,
        mock_manager,
        mock_chat_agent,
    ):
        """
        Empty conversations should still produce an assistant reply.
        """

        from apps.ai_agents.services import generate_chat_reply

        session = MagicMock()
        memory = MagicMock()

        memory.transcript.return_value = ""

        mock_chat_service.get_or_create_active_session.return_value = session

        mock_build_memory.return_value = memory

        manager = MagicMock()
        manager.optimize_memory.return_value = memory
        mock_manager.return_value = manager

        agent = MagicMock()
        agent.reply.return_value = "Hello!"
        mock_chat_agent.return_value = agent

        response = generate_chat_reply(
            trip=self.trip,
            user_message="Hi",
        )

        self.assertEqual(
            response,
            "Hello!",
        )

        mock_chat_service.add_assistant_message.assert_called_once()

    @patch("apps.ai_agents.services.ChatAgent")
    @patch("apps.ai_agents.services.ConversationManager")
    @patch("apps.ai_agents.services.ConversationMemoryAdapter.build_memory")
    @patch("apps.ai_agents.services.ChatService")
    def test_generate_chat_reply_strips_response(
        self,
        mock_chat_service,
        mock_build_memory,
        mock_manager,
        mock_chat_agent,
    ):
        """
        Assistant responses should be stripped before persistence.
        """

        from apps.ai_agents.services import generate_chat_reply

        session = MagicMock()
        memory = MagicMock()

        memory.transcript.return_value = ""

        mock_chat_service.get_or_create_active_session.return_value = session

        mock_build_memory.return_value = memory

        manager = MagicMock()
        manager.optimize_memory.return_value = memory
        mock_manager.return_value = manager

        agent = MagicMock()
        agent.reply.return_value = "   Welcome!   "
        mock_chat_agent.return_value = agent

        response = generate_chat_reply(
            trip=self.trip,
            user_message="Hello",
        )

        mock_chat_service.add_assistant_message.assert_called_once_with(
            session=session,
            content="Welcome!",
        )

        self.assertEqual(
            response,
            "Welcome!",
        )
    
    @patch("apps.ai_agents.services.search_destination")
    @patch("apps.ai_agents.services.ChatAgent")
    def test_passes_retrieved_destinations_to_chat_agent(
        self,
        mock_chat_agent,
        mock_search_destination,
    ):
        """
        Retrieved destinations should be forwarded to the ChatAgent.
        """

        from decimal import Decimal
        from unittest.mock import ANY

        from ai.tools.destination_search import (
            DestinationSearchResult,
        )

        from apps.ai_agents.services import (
            generate_chat_reply,
        )

        mock_search_destination.return_value = [
            DestinationSearchResult(
                name="Tokyo",
                country="Japan",
                city="Tokyo",
                latitude=Decimal("35.676200"),
                longitude=Decimal("139.650300"),
                summary="City of Light",
                description="Capital of France",
                tags=["culture", "museum"],
            ),
        ]

        agent = mock_chat_agent.return_value
        agent.reply.return_value = "Welcome!"

        response = generate_chat_reply(
            trip=self.trip,
            user_message="Tokyo",
        )

        mock_search_destination.assert_called_once_with(
            query="Tokyo",
        )

        agent.reply.assert_called_once_with(
            conversation_context=ANY,
            user_message="Tokyo",
            retrieved_destinations=mock_search_destination.return_value,
        )

        self.assertEqual(
            response,
            "Welcome!",
        )
    
        
class AttachDestinationContextTests(BaseServiceTestCase):
    """
    Tests for attaching destination retrieval context.
    """

    @patch("apps.ai_agents.services.search_destination")
    def test_attaches_destination_results(
        self,
        mock_search_destination,
    ):
        from ai.tools.destination_search import (
            DestinationSearchResult,
        )

        from apps.ai_agents.services import (
            _attach_destination_context,
        )

        mock_search_destination.return_value = [
            DestinationSearchResult(
                name="Tokyo",
                country="Japan",
                city="Tokyo",
                latitude=Decimal("35.676200"),
                longitude=Decimal("139.650300"),
                summary="City of Light",
                description="Capital of France",
                tags=["culture", "museum"],
                
            ),
        ]

        state = {}

        result = _attach_destination_context(
            state=state,
            user_message="Tokyo",
        )

        mock_search_destination.assert_called_once_with(
            query="Tokyo",
        )

        self.assertIn(
            "retrieved_destinations",
            result,
        )

        self.assertEqual(
            len(result["retrieved_destinations"]),
            1,
        )

    @patch("apps.ai_agents.services.search_destination")
    def test_returns_original_state_when_no_destinations_found(
        self,
        mock_search_destination,
    ):
        from apps.ai_agents.services import (
            _attach_destination_context,
        )

        mock_search_destination.return_value = []

        state = {
            "trip_title": self.trip.title,
        }

        result = _attach_destination_context(
            state=state,
            user_message="Unknown Place",
        )

        mock_search_destination.assert_called_once_with(
            query="Unknown Place",
        )

        self.assertEqual(
            result,
            state,
        )

        self.assertNotIn(
            "retrieved_destinations",
            result,
        )