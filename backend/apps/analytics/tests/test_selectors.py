from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_agents.models import AgentRun, AgentRunStatus, AgentType
from apps.analytics.selectors import (
    get_agent_performance_summary,
    get_booking_intent_summary,
    get_platform_summary,
    get_recommendation_acceptance_rate,
)
from apps.bookings.models import Booking, BookingType
from apps.recommendations.models import (
    Recommendation,
    RecommendationCategory,
    RecommendationStatus,
)
from apps.destinations.models import Destination
from apps.trips.models import Trip, TripStatus

User = get_user_model()


class AnalyticsSelectorBaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="analytics@example.com",
            password="pass1234",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            title="Analytics Trip",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )


class GetPlatformSummarySelectorTests(AnalyticsSelectorBaseTests):
    def setUp(self):
        super().setUp()
        Trip.objects.create(
            user=self.user,
            title="Draft Trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 3),
            status=TripStatus.DRAFT,
        )
        Trip.objects.create(
            user=self.user,
            title="Planned Trip",
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 3),
            status=TripStatus.PLANNED,
        )
        AgentRun.objects.create(
            trip=self.trip,
            agent_type=AgentType.FULL_GRAPH,
            status=AgentRunStatus.SUCCEEDED,
        )
        AgentRun.objects.create(
            trip=self.trip,
            agent_type=AgentType.FULL_GRAPH,
            status=AgentRunStatus.FAILED,
        )

    def test_trip_and_agent_counts_are_correct(self):
        summary = get_platform_summary()

        self.assertEqual(summary["total_trips"], 3)
        self.assertEqual(summary["trips_by_status"]["draft"], 2)
        self.assertEqual(summary["trips_by_status"]["planned"], 1)
        self.assertEqual(summary["total_agent_runs"], 2)
        self.assertEqual(summary["agent_success_rate"], 0.5)

    def test_uses_two_aggregate_queries(self):
        with self.assertNumQueries(2):
            get_platform_summary()


class GetAgentPerformanceSummaryTests(AnalyticsSelectorBaseTests):
    def setUp(self):
        super().setUp()
        AgentRun.objects.create(
            trip=self.trip,
            agent_type=AgentType.FULL_GRAPH,
            status=AgentRunStatus.SUCCEEDED,
        )
        AgentRun.objects.create(
            trip=self.trip,
            agent_type=AgentType.FULL_GRAPH,
            status=AgentRunStatus.SUCCEEDED,
        )
        AgentRun.objects.create(
            trip=self.trip,
            agent_type=AgentType.FULL_GRAPH,
            status=AgentRunStatus.FAILED,
        )
        AgentRun.objects.create(
            trip=self.trip,
            agent_type=AgentType.FULL_GRAPH,
            status=AgentRunStatus.PENDING,
        )

    def test_counts_are_correct(self):
        summary = get_agent_performance_summary()

        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["succeeded"], 2)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["needs_review"], 0)
        self.assertEqual(summary["pending_or_running"], 1)

    def test_single_query(self):
        with self.assertNumQueries(1):
            get_agent_performance_summary()


class GetRecommendationAcceptanceRateTests(AnalyticsSelectorBaseTests):
    def setUp(self):
        super().setUp()
        destination = Destination.objects.create(
            name="Kochi",
            country="India",
            city="Kochi",
            latitude="9.9312",
            longitude="76.2673",
        )
        for status in (
            RecommendationStatus.ACCEPTED,
            RecommendationStatus.REJECTED,
            RecommendationStatus.PENDING,
        ):
            Recommendation.objects.create(
                trip=self.trip,
                destination=destination,
                category=RecommendationCategory.ATTRACTION,
                score="0.90",
                reason="Analytics test recommendation.",
                status=status,
            )

    def test_pending_is_excluded_from_denominator(self):
        self.assertEqual(get_recommendation_acceptance_rate(), 0.5)

    def test_empty_decision_set_returns_zero(self):
        Recommendation.objects.all().delete()
        self.assertEqual(get_recommendation_acceptance_rate(), 0.0)


class GetBookingIntentSummaryTests(AnalyticsSelectorBaseTests):
    def setUp(self):
        super().setUp()
        Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.FLIGHT,
            title="Flight",
        )
        Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.HOTEL,
            title="Hotel",
        )
        Booking.objects.create(
            trip=self.trip,
            booking_type=BookingType.ACTIVITY,
            title="Activity",
        )

    def test_booking_counts_are_correct(self):
        summary = get_booking_intent_summary()

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["from_recommendation"], 0)
        self.assertEqual(summary["flights"], 1)
        self.assertEqual(summary["hotels"], 1)
        self.assertEqual(summary["activities"], 1)

    def test_single_query(self):
        with self.assertNumQueries(1):
            get_booking_intent_summary()
