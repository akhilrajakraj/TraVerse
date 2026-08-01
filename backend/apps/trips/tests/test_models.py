"""
Model tests for the Trips application.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.trips.models import (
    Trip,
    TripStatus,
)

User = get_user_model()


class TripModelTests(TestCase):
    """
    Test suite for the Trip model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="traveler@example.com",
            password="Password123!",
        )

        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Vacation",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
        )

        self.trip.destinations.add(
            self.destination,
        )

    def test_trip_creation(self):
        """
        Verify a Trip instance is created successfully.
        """

        self.assertEqual(
            Trip.objects.count(),
            1,
        )

    def test_default_status(self):
        """
        Verify new trips start in the draft state.
        """

        self.assertEqual(
            self.trip.status,
            TripStatus.DRAFT,
        )

    def test_duration_days_property(self):
        """
        Verify the inclusive duration calculation.
        """

        self.assertEqual(
            self.trip.duration_days,
            5,
        )

    def test_string_representation(self):
        """
        Verify the model string representation.
        """

        self.assertEqual(
            str(self.trip),
            "Japan Vacation (traveler@example.com)",
        )

    def test_destination_relationship(self):
        """
        Verify destinations can be associated with a trip.
        """

        self.assertEqual(
            self.trip.destinations.count(),
            1,
        )

        self.assertEqual(
            self.trip.destinations.first(),
            self.destination,
        )

    def test_uuid_primary_key_exists(self):
        """
        Verify the Trip model uses a UUID primary key.
        """

        self.assertIsNotNone(
            self.trip.id,
        )