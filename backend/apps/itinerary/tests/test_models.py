"""
Model tests for the Itinerary application.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.destinations.models import Destination
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)
from apps.trips.models import Trip


User = get_user_model()


class ItineraryModelTests(TestCase):
    """
    Test suite for itinerary domain models.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="Password123!",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Trip",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
        )

        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        self.day = ItineraryDay.objects.create(
            trip=self.trip,
            date=date(2026, 4, 1),
            day_number=1,
            summary="Arrival",
        )

    def test_create_itinerary_day(self):
        """
        An itinerary day should be created successfully.
        """

        self.assertEqual(
            self.day.trip,
            self.trip,
        )

        self.assertEqual(
            self.day.day_number,
            1,
        )

    def test_unique_day_number_constraint(self):
        """
        A trip cannot contain duplicate day numbers.
        """

        with self.assertRaises(IntegrityError):
            ItineraryDay.objects.create(
                trip=self.trip,
                date=date(2026, 4, 2),
                day_number=1,
            )

    def test_unique_date_constraint(self):
        """
        A trip cannot contain duplicate dates.
        """

        with self.assertRaises(IntegrityError):
            ItineraryDay.objects.create(
                trip=self.trip,
                date=date(2026, 4, 1),
                day_number=2,
            )

    def test_create_itinerary_item(self):
        """
        Itinerary items should default to gap ordering.
        """

        item = ItineraryItem.objects.create(
            day=self.day,
            destination=self.destination,
            title="Visit Tokyo Tower",
        )

        self.assertEqual(
            item.order,
            10,
        )

    def test_destination_set_null(self):
        """
        Removing a destination must not delete itinerary items.
        """

        item = ItineraryItem.objects.create(
            day=self.day,
            destination=self.destination,
            title="Visit Temple",
        )

        self.destination.delete()

        item.refresh_from_db()

        self.assertIsNone(
            item.destination,
        )

    def test_string_representations(self):
        """
        Models should provide meaningful string representations.
        """

        item = ItineraryItem.objects.create(
            day=self.day,
            title="Breakfast",
        )

        self.assertIn(
            "Day 1",
            str(self.day),
        )

        self.assertEqual(
            str(item),
            f"Breakfast ({self.day})",
        )