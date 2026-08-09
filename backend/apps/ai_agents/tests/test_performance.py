from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from ai.agents.schemas import (
    BudgetEstimateSchema,
    BudgetLineItemEstimateSchema,
    DailyWeatherSchema,
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
    PackingItemSchema,
    PackingListSchema,
    RecommendationBatchSchema,
    RecommendationItemSchema,
    WeatherForecastSchema,
)

from apps.ai_agents.services import run_travel_planner
from apps.destinations.models import Destination
from apps.trips.models import Trip


User = get_user_model()


class FullPlanningRunPerformanceTests(TestCase):
    """
    Establish a combined query-count ceiling for the complete planning
    service call rather than asserting isolated persistence helpers only.

    The chapter's 25-query value is treated as a ceiling. Django's
    assertNumQueries() is an exact-count assertion, so CaptureQueriesContext
    is used here to express the intended <= 25 contract without pretending
    that 25 is a required target.

    The Trip passed to the service is fetched the same way the real Celery
    worker fetches it. This keeps the measurement focused on the service
    execution rather than charging the service for a relation that the
    production worker has already prefetched.
    """

    QUERY_CEILING = 25

    def setUp(self):
        self.user = User.objects.create_user(
            email="performance@example.com",
            password="Password123!",
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
            title="Performance Test",
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
            traveler_count=2,
        )
        self.trip.destinations.add(self.destination)

    def test_full_run_stays_under_query_ceiling(self):
        plan = ItineraryPlanSchema(
            days=[
                ItineraryDaySchema(
                    day_number=1,
                    date=date(2026, 9, 10),
                    summary="Arrival",
                    items=[
                        ItineraryItemSchema(
                            title="Check in",
                            description="Hotel check-in",
                            start_time=time(14, 0),
                            estimated_cost_usd=20.0,
                        )
                    ],
                )
            ]
        )
        budget = BudgetEstimateSchema(
            line_items=[
                BudgetLineItemEstimateSchema(
                    category="food",
                    description="Dinner",
                    estimated_amount=20.0,
                )
            ]
        )
        weather = WeatherForecastSchema(
            days=[
                DailyWeatherSchema(
                    date=date(2026, 9, 10),
                    condition="Clear",
                    high_f=80.0,
                    low_f=68.0,
                    precipitation_chance=10,
                )
            ]
        )
        recommendations = RecommendationBatchSchema(
            recommendations=[
                RecommendationItemSchema(
                    destination="Kyoto",
                    category="attraction",
                    score=0.9,
                    reason="Historic temples and gardens.",
                )
            ]
        )
        packing = PackingListSchema(
            items=[
                PackingItemSchema(
                    category="documents",
                    item="Passport",
                    quantity=1,
                    reason="Required for international travel.",
                )
            ]
        )

        graph_state = {
            "itinerary": plan,
            "budget_estimate": budget,
            "weather_forecast": weather,
            "recommendations": recommendations,
            "packing_list": packing,
        }

        planning_trip = (
            Trip.objects
            .select_related("user")
            .prefetch_related("destinations")
            .get(pk=self.trip.pk)
        )

        with (
            patch("apps.ai_agents.services.run_planning_graph", return_value=graph_state),
            patch("apps.notifications.tasks.send_notification_task.delay"),
            CaptureQueriesContext(connection) as queries,
        ):
            run_travel_planner(
                trip=planning_trip,
                triggered_by=self.user,
            )

        query_count = len(queries)
        if query_count > self.QUERY_CEILING:
            captured_sql = "\n".join(
                f"{index}. {query['sql']}"
                for index, query in enumerate(queries, start=1)
            )
            self.fail(
                "Full planning run exceeded the query ceiling: "
                f"{query_count} queries executed; "
                f"ceiling is {self.QUERY_CEILING}.\n\n"
                "Captured SQL:\n"
                f"{captured_sql}"
            )


class PlanningWorkerQueryShapeTests(TestCase):
    """Verify the async worker preloads the planning hot-path relation."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="worker-performance@example.com",
            password="Password123!",
        )
        self.destination = Destination.objects.create(
            name="Paris",
            country="France",
            city="Paris",
            latitude=Decimal("48.856600"),
            longitude=Decimal("2.352200"),
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title="Worker Performance Test",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 2),
            traveler_count=1,
        )
        self.trip.destinations.add(self.destination)

    @patch("apps.ai_agents.services.run_travel_planner")
    def test_worker_fetches_destinations_with_trip(self, mock_run):
        from apps.ai_agents.tasks import run_travel_planner_task

        mock_run.return_value.id = self.trip.id

        with CaptureQueriesContext(connection) as queries:
            run_travel_planner_task.run(
                trip_id=str(self.trip.id),
                user_id=self.user.id,
            )

        self.assertEqual(len(queries), 3)
        fetched_trip = mock_run.call_args.kwargs["trip"]
        self.assertIn("destinations", fetched_trip._prefetched_objects_cache)
