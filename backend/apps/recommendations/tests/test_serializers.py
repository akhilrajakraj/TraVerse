"""
Serializer tests for the Recommendations application.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.recommendations.models import (
    Recommendation,
    RecommendationCategory,
)
from apps.recommendations.serializers import (
    RecommendationSerializer,
)
from apps.trips.models import Trip

User = get_user_model()


class RecommendationSerializerTests(TestCase):
    """
    Validate RecommendationSerializer.
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

        self.recommendation = Recommendation.objects.create(
            trip=self.trip,
            destination=self.destination,
            category=RecommendationCategory.ATTRACTION,
            score=Decimal("0.95"),
            reason="Excellent cultural experience.",
        )

    def test_serializer_contains_expected_fields(self):
        serializer = RecommendationSerializer(
            self.recommendation,
        )

        expected = {
            "id",
            "category",
            "score",
            "reason",
            "status",
            "is_ai_generated",
            "destination",
            "created_at",
        }

        self.assertEqual(
            set(serializer.data.keys()),
            expected,
        )

    def test_nested_destination_is_serialized(self):
        serializer = RecommendationSerializer(
            self.recommendation,
        )

        self.assertEqual(
            serializer.data["destination"]["name"],
            "Kyoto",
        )

        self.assertEqual(
            serializer.data["destination"]["country"],
            "Japan",
        )

    def test_reason_is_serialized(self):
        serializer = RecommendationSerializer(
            self.recommendation,
        )

        self.assertEqual(
            serializer.data["reason"],
            "Excellent cultural experience.",
        )

    def test_ai_generated_defaults_to_true(self):
        serializer = RecommendationSerializer(
            self.recommendation,
        )

        self.assertTrue(
            serializer.data["is_ai_generated"],
        )