"""
Management command tests for the Recommendations application.
"""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.destinations.models import Destination
from apps.recommendations.models import Recommendation
from apps.trips.models import Trip

User = get_user_model()


class SeedFakeRecommendationsCommandTests(TestCase):
    """
    Validate the seed_fake_recommendations management command.
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

        self.trip.destinations.add(
            self.destination,
        )

    def test_seed_default_number_of_recommendations(self):
        call_command(
            "seed_fake_recommendations",
            str(self.trip.id),
        )

        self.assertEqual(
            Recommendation.objects.filter(
                trip=self.trip,
            ).count(),
            5,
        )

    def test_seed_custom_number_of_recommendations(self):
        call_command(
            "seed_fake_recommendations",
            str(self.trip.id),
            "--count",
            "10",
        )

        self.assertEqual(
            Recommendation.objects.filter(
                trip=self.trip,
            ).count(),
            10,
        )

    def test_invalid_trip_raises_command_error(self):
        with self.assertRaises(
            CommandError,
        ):
            call_command(
                "seed_fake_recommendations",
                "00000000-0000-0000-0000-000000000000",
            )

    def test_command_outputs_success_message(self):
        stdout = StringIO()

        call_command(
            "seed_fake_recommendations",
            str(self.trip.id),
            stdout=stdout,
        )

        self.assertIn(
            "Successfully created",
            stdout.getvalue(),
        )