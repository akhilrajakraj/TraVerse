"""
Selector tests for the Recommendations application.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.recommendations.models import (
    Recommendation,
    RecommendationCategory,
    RecommendationStatus,
)
from apps.recommendations.selectors import (
    get_accepted_recommendations,
    get_pending_recommendations,
    get_rejected_recommendations,
    get_trip_recommendations,
)
from apps.trips.models import Trip

User = get_user_model()


class RecommendationSelectorTests(TestCase):
    """
    Validate recommendation selectors.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="password123",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
        )

        self.other_trip = Trip.objects.create(
            user=self.user,
            title="Europe Trip",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
        )

        self.destination = Destination.objects.create(
            name="Kyoto",
            country="Japan",
            city="Kyoto",
            latitude=Decimal("35.011600"),
            longitude=Decimal("135.768100"),
            is_active=True,
        )

    def create_recommendation(
        self,
        trip=None,
        status=RecommendationStatus.PENDING,
        score="0.90",
    ):
        return Recommendation.objects.create(
            trip=trip or self.trip,
            destination=self.destination,
            category=RecommendationCategory.ATTRACTION,
            score=Decimal(score),
            reason="Recommended destination.",
            status=status,
        )

    def test_get_trip_recommendations(self):
        first = self.create_recommendation(score="0.75")
        second = self.create_recommendation(score="0.95")

        self.create_recommendation(
            trip=self.other_trip,
            score="0.99",
        )

        recommendations = list(
            get_trip_recommendations(
                self.trip,
            )
        )

        self.assertEqual(
            len(recommendations),
            2,
        )

        self.assertEqual(
            recommendations[0],
            second,
        )

        self.assertEqual(
            recommendations[1],
            first,
        )

    def test_get_pending_recommendations(self):
        pending = self.create_recommendation(
            status=RecommendationStatus.PENDING,
        )

        self.create_recommendation(
            status=RecommendationStatus.ACCEPTED,
        )

        recommendations = list(
            get_pending_recommendations(
                self.trip,
            )
        )

        self.assertEqual(
            recommendations,
            [pending],
        )

    def test_get_accepted_recommendations(self):
        accepted = self.create_recommendation(
            status=RecommendationStatus.ACCEPTED,
        )

        self.create_recommendation(
            status=RecommendationStatus.REJECTED,
        )

        recommendations = list(
            get_accepted_recommendations(
                self.trip,
            )
        )

        self.assertEqual(
            recommendations,
            [accepted],
        )

    def test_get_rejected_recommendations(self):
        rejected = self.create_recommendation(
            status=RecommendationStatus.REJECTED,
        )

        self.create_recommendation(
            status=RecommendationStatus.PENDING,
        )

        recommendations = list(
            get_rejected_recommendations(
                self.trip,
            )
        )

        self.assertEqual(
            recommendations,
            [rejected],
        )