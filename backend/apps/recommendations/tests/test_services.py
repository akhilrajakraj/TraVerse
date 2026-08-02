"""
Service tests for the Recommendations application.
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
from apps.recommendations.services import (
    accept_recommendation,
    reject_recommendation,
)
from apps.trips.models import Trip

User = get_user_model()


class RecommendationServiceTests(TestCase):
    """
    Validate recommendation services.
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

        self.destination = Destination.objects.create(
            name="Kyoto",
            country="Japan",
            city="Kyoto",
            latitude=Decimal("35.011600"),
            longitude=Decimal("135.768100"),
            is_active=True,
        )

    def create_recommendation(self):
        return Recommendation.objects.create(
            trip=self.trip,
            destination=self.destination,
            category=RecommendationCategory.ATTRACTION,
            score=Decimal("0.95"),
            reason="Recommended destination.",
        )

    def test_accept_recommendation(self):
        recommendation = self.create_recommendation()

        self.assertEqual(
            recommendation.status,
            RecommendationStatus.PENDING,
        )

        updated = accept_recommendation(
            recommendation,
        )

        updated.refresh_from_db()

        self.assertEqual(
            updated.status,
            RecommendationStatus.ACCEPTED,
        )

    def test_reject_recommendation(self):
        recommendation = self.create_recommendation()

        updated = reject_recommendation(
            recommendation,
        )

        updated.refresh_from_db()

        self.assertEqual(
            updated.status,
            RecommendationStatus.REJECTED,
        )

    def test_accept_returns_same_instance(self):
        recommendation = self.create_recommendation()

        updated = accept_recommendation(
            recommendation,
        )

        self.assertEqual(
            updated.pk,
            recommendation.pk,
        )

    def test_reject_returns_same_instance(self):
        recommendation = self.create_recommendation()

        updated = reject_recommendation(
            recommendation,
        )

        self.assertEqual(
            updated.pk,
            recommendation.pk,
        )