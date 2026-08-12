"""Management-command tests for the Recommendations application."""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.destinations.models import Destination
from apps.recommendations.models import Recommendation
from apps.trips.models import Trip

User = get_user_model()


class SeedFakeRecommendationsCommandTests(TestCase):
    """Validate the development-only fake recommendation seed command."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="seed@example.com",
            password="password123",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Seed Trip",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
        )

        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=Decimal("35.676200"),
            longitude=Decimal("139.650300"),
            is_active=True,
        )

    def test_seed_creates_requested_count(self):
        call_command(
            "seed_fake_recommendations",
            str(self.trip.id),
            "--count",
            "4",
            stdout=StringIO(),
        )

        recommendations = Recommendation.objects.filter(
            trip=self.trip,
        )

        self.assertEqual(recommendations.count(), 4)
        self.assertTrue(
            all(item.is_ai_generated for item in recommendations)
        )
        self.assertTrue(
            all("" < str(item.score) <= "0.99" for item in recommendations)
        )

    def test_seed_falls_back_to_active_catalog_destination(self):
        empty_trip = Trip.objects.create(
            user=self.user,
            title="No Linked Destinations",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 5),
        )

        call_command(
            "seed_fake_recommendations",
            str(empty_trip.id),
            "--count",
            "2",
            stdout=StringIO(),
        )

        self.assertEqual(
            Recommendation.objects.filter(trip=empty_trip).count(),
            2,
        )

        self.assertEqual(
            Recommendation.objects.filter(trip=empty_trip).first().destination,
            self.destination,
        )
