"""
Serializer tests for the Itinerary application.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)
from apps.itinerary.serializers import (
    AddItineraryItemSerializer,
    ItineraryDaySerializer,
    ItineraryItemSerializer,
)
from apps.trips.models import Trip


User = get_user_model()


class ItinerarySerializerTests(TestCase):
    """
    Test suite for itinerary serializers.
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

        self.item = ItineraryItem.objects.create(
            day=self.day,
            destination=self.destination,
            title="Visit Tokyo Tower",
            description="Morning visit",
            order=10,
        )

    def test_itinerary_item_serializer(self):
        """
        Item serializer should expose nested destination data.
        """

        serializer = ItineraryItemSerializer(
            self.item,
        )

        self.assertEqual(
            serializer.data["title"],
            "Visit Tokyo Tower",
        )

        self.assertEqual(
            serializer.data["destination"]["name"],
            "Tokyo",
        )

    def test_itinerary_day_serializer(self):
        """
        Day serializer should include nested itinerary items.
        """

        serializer = ItineraryDaySerializer(
            self.day,
        )

        self.assertEqual(
            serializer.data["day_number"],
            1,
        )

        self.assertEqual(
            len(serializer.data["items"]),
            1,
        )

    def test_add_item_serializer_valid(self):
        """
        Add serializer should accept valid payloads.
        """

        serializer = AddItineraryItemSerializer(
            data={
                "title": "Lunch",
                "description": "Sushi",
                "destination_id": str(
                    self.destination.id,
                ),
            },
        )

        self.assertTrue(
            serializer.is_valid(),
        )

    def test_add_item_serializer_requires_title(self):
        """
        Title is required.
        """

        serializer = AddItineraryItemSerializer(
            data={},
        )

        self.assertFalse(
            serializer.is_valid(),
        )