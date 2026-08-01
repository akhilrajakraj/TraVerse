"""
Service layer tests for the Itinerary application.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.itinerary import services
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)
from apps.trips.models import Trip


User = get_user_model()


class ItineraryServiceTests(TestCase):
    """
    Test suite for itinerary service layer.
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

        self.day = ItineraryDay.objects.create(
            trip=self.trip,
            date=date(2026, 4, 1),
            day_number=1,
        )

        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

    def test_add_first_item(self):
        """
        First item should receive order 10.
        """

        item = services.add_item_to_day(
            day=self.day,
            title="Breakfast",
        )

        self.assertEqual(
            item.order,
            10,
        )

    def test_add_second_item(self):
        """
        Second item should receive order 20.
        """

        services.add_item_to_day(
            day=self.day,
            title="Breakfast",
        )

        second = services.add_item_to_day(
            day=self.day,
            title="Museum",
        )

        self.assertEqual(
            second.order,
            20,
        )

    def test_insert_between_items(self):
        """
        Items inserted between two existing items should use the
        midpoint order value.
        """

        first = services.add_item_to_day(
            day=self.day,
            title="Breakfast",
        )

        second = services.add_item_to_day(
            day=self.day,
            title="Dinner",
        )

        inserted = services.insert_item_between(
            day=self.day,
            title="Museum",
            before=first,
            after=second,
        )

        self.assertEqual(
            inserted.order,
            15,
        )

    def test_renumber_day(self):
        """
        Renumbering should restore gap ordering.
        """

        item1 = ItineraryItem.objects.create(
            day=self.day,
            title="A",
            order=3,
        )

        item2 = ItineraryItem.objects.create(
            day=self.day,
            title="B",
            order=4,
        )

        services.renumber_day(
            day=self.day,
        )

        item1.refresh_from_db()
        item2.refresh_from_db()

        self.assertEqual(
            item1.order,
            10,
        )

        self.assertEqual(
            item2.order,
            20,
        )

    def test_add_item_with_destination(self):
        """
        Destination association should be preserved.
        """

        item = services.add_item_to_day(
            day=self.day,
            title="Tokyo Tower",
            destination=self.destination,
        )

        self.assertEqual(
            item.destination,
            self.destination,
        )