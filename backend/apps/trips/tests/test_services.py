"""
Service layer tests for the Trips application.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.trips.exceptions import (
    InvalidDateRange,
    InvalidStatusTransition,
)
from apps.trips.models import (
    Trip,
    TripStatus,
)
from apps.trips import services


User = get_user_model()


class TripServiceTests(TestCase):
    """
    Test suite for Trip service functions.
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

    def test_create_trip(self):
        """
        Verify trip creation through the service layer.
        """

        trip = services.create_trip(
            user=self.user,
            title="Japan Trip",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            destination_ids=[
                self.destination.pk,
            ],
        )

        self.assertEqual(
            trip.title,
            "Japan Trip",
        )

        self.assertEqual(
            trip.user,
            self.user,
        )

        self.assertEqual(
            trip.status,
            TripStatus.DRAFT,
        )

        self.assertEqual(
            trip.destinations.count(),
            1,
        )

    def test_invalid_date_range(self):
        """
        Invalid travel dates should raise an exception.
        """

        with self.assertRaises(
            InvalidDateRange,
        ):
            services.create_trip(
                user=self.user,
                title="Invalid Trip",
                start_date=date.today(),
                end_date=date.today() - timedelta(days=1),
            )

    def test_update_trip_dates(self):
        """
        Verify updating trip dates.
        """

        trip = services.create_trip(
            user=self.user,
            title="Japan Trip",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
        )

        updated_trip = services.update_trip_dates(
            trip=trip,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=6),
        )

        self.assertEqual(
            updated_trip.duration_days,
            7,
        )

    def test_valid_status_transition(self):
        """
        Verify a valid lifecycle transition.
        """

        trip = services.create_trip(
            user=self.user,
            title="Japan Trip",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
        )

        services.transition_trip_status(
            trip=trip,
            new_status=TripStatus.PLANNING,
        )

        trip.refresh_from_db()

        self.assertEqual(
            trip.status,
            TripStatus.PLANNING,
        )

    def test_invalid_status_transition(self):
        """
        Invalid lifecycle transitions should raise an exception.
        """

        trip = services.create_trip(
            user=self.user,
            title="Japan Trip",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
        )

        with self.assertRaises(
            InvalidStatusTransition,
        ):
            services.transition_trip_status(
                trip=trip,
                new_status=TripStatus.COMPLETED,
            )