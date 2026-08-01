"""
Selector tests for the Itinerary application.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)
from apps.itinerary.selectors import get_trip_itinerary
from apps.trips.models import Trip


User = get_user_model()


class ItinerarySelectorTests(TestCase):
    """
    Test suite for itinerary selectors.
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
            end_date=date(2026, 4, 3),
        )

        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
        )

        self.day1 = ItineraryDay.objects.create(
            trip=self.trip,
            date=date(2026, 4, 1),
            day_number=1,
        )

        self.day2 = ItineraryDay.objects.create(
            trip=self.trip,
            date=date(2026, 4, 2),
            day_number=2,
        )

        ItineraryItem.objects.create(
            day=self.day1,
            title="Breakfast",
            order=10,
            destination=self.destination,
        )

        ItineraryItem.objects.create(
            day=self.day1,
            title="Temple",
            order=20,
            destination=self.destination,
        )

        ItineraryItem.objects.create(
            day=self.day2,
            title="Museum",
            order=10,
            destination=self.destination,
        )

    def test_returns_all_days(self):
        """
        Selector should return every itinerary day.
        """

        result = get_trip_itinerary(
            trip=self.trip,
        )

        self.assertEqual(
            len(result),
            2,
        )

    def test_days_are_ordered(self):
        """
        Days should be ordered by day_number.
        """

        result = get_trip_itinerary(
            trip=self.trip,
        )

        self.assertEqual(
            result[0].day_number,
            1,
        )

        self.assertEqual(
            result[1].day_number,
            2,
        )

    def test_items_are_ordered(self):
        """
        Items should already be ordered.
        """

        result = get_trip_itinerary(
            trip=self.trip,
        )

        items = list(
            result[0].items.all()
        )

        self.assertEqual(
            items[0].order,
            10,
        )

        self.assertEqual(
            items[1].order,
            20,
        )

    def test_destination_is_prefetched(self):
        """
        Destination relation should already be loaded.
        """

        with self.assertNumQueries(2):

            result = get_trip_itinerary(
                trip=self.trip,
            )

            for day in result:

                for item in day.items.all():

                    if item.destination:

                        _ = item.destination.name