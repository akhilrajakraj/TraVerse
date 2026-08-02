"""
Model tests for the Recommendations application.
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
from apps.trips.models import Trip

User = get_user_model()


class RecommendationModelTests(TestCase):
    """
    Validate Recommendation model behavior.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="pass1234",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
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
        **kwargs,
    ):
        """
        Create a recommendation using sensible defaults.
        """

        defaults = {
            "trip": self.trip,
            "destination": self.destination,
            "category": RecommendationCategory.ATTRACTION,
            "score": Decimal("0.90"),
            "reason": "Recommended destination.",
        }

        defaults.update(kwargs)

        return Recommendation.objects.create(
            **defaults,
        )

    def test_create_recommendation(self):
        recommendation = self.create_recommendation(
            category=RecommendationCategory.ATTRACTION,
            score=Decimal("0.95"),
            reason="Excellent cultural experience.",
        )

        self.assertEqual(
            recommendation.trip,
            self.trip,
        )

        self.assertEqual(
            recommendation.destination,
            self.destination,
        )

        self.assertEqual(
            recommendation.status,
            RecommendationStatus.PENDING,
        )

        self.assertTrue(
            recommendation.is_ai_generated,
        )

    def test_string_representation(self):
        recommendation = self.create_recommendation(
            category=RecommendationCategory.RESTAURANT,
            score=Decimal("0.80"),
            reason="Great local cuisine.",
        )

        self.assertEqual(
            str(recommendation),
            "Kyoto (0.80)",
        )

    def test_default_status_is_pending(self):
        recommendation = self.create_recommendation(
            category=RecommendationCategory.HOTEL,
            score=Decimal("0.75"),
            reason="Comfortable accommodation.",
        )

        self.assertEqual(
            recommendation.status,
            RecommendationStatus.PENDING,
        )

    def test_default_ai_flag_is_true(self):
        recommendation = self.create_recommendation(
            category=RecommendationCategory.SHOPPING,
            score=Decimal("0.70"),
            reason="Excellent shopping district.",
        )

        self.assertTrue(
            recommendation.is_ai_generated,
        )

    def test_ordering_by_score_descending(self):
        low = self.create_recommendation(
            category=RecommendationCategory.RESTAURANT,
            score=Decimal("0.55"),
            reason="Low score.",
        )

        high = self.create_recommendation(
            category=RecommendationCategory.RESTAURANT,
            score=Decimal("0.98"),
            reason="High score.",
        )

        recommendations = list(
            Recommendation.objects.all()
        )

        self.assertEqual(
            recommendations[0],
            high,
        )

        self.assertEqual(
            recommendations[1],
            low,
        )

    def test_reason_is_stored(self):
        recommendation = self.create_recommendation(
            category=RecommendationCategory.EXPERIENCE,
            score=Decimal("0.91"),
            reason="Recommended because of exceptional reviews.",
        )

        self.assertEqual(
            recommendation.reason,
            "Recommended because of exceptional reviews.",
        )