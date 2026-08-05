"""
Serializer tests for the Trips application.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.destinations.models import Destination
from apps.trips.models import (
    Trip,
    PackingItem,
    PackingCategory,
)
from apps.trips.serializers import (
    TripSerializer,
    PackingItemSerializer,
)


User = get_user_model()


class TripSerializerTests(TestCase):
    """
    Test suite for the Trip serializer.
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

    def test_serializer_contains_expected_fields(self):
        """
        Verify serializer output fields.
        """

        serializer = TripSerializer(
            self.trip,
        )

        expected_fields = {
            "id",
            "title",
            "start_date",
            "end_date",
            "duration_days",
            "status",
            "traveler_count",
            "notes",
            "computed_budget_total",
            "destinations",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(serializer.data.keys()),
            expected_fields,
        )

    def test_duration_days_is_serialized(self):
        """
        Verify computed duration is exposed.
        """

        serializer = TripSerializer(
            self.trip,
        )

        self.assertEqual(
            serializer.data["duration_days"],
            5,
        )

    def test_nested_destinations_are_serialized(self):
        """
        Verify destination objects are nested.
        """

        serializer = TripSerializer(
            self.trip,
        )

        self.assertEqual(
            len(serializer.data["destinations"]),
            1,
        )

        self.assertEqual(
            serializer.data["destinations"][0]["name"],
            "Tokyo",
        )
        
class PackingItemSerializerTests(TestCase):
    """
    Test suite for the PackingItemSerializer.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="traveler@example.com",
            password="Password123!",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Vacation",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=5),
        )

        self.item = PackingItem.objects.create(
            trip=self.trip,
            category=PackingCategory.CLOTHING,
            item="Rain Jacket",
            quantity=1,
            reason="Expected rain during the trip.",
        )

    def test_serializer_contains_expected_fields(self):
        """
        Verify serializer exposes the expected fields.
        """

        serializer = PackingItemSerializer(
            self.item,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "category",
                "item",
                "quantity",
                "reason",
                "is_ai_generated",
                "created_at",
                "updated_at",
            },
        )

    def test_serializer_returns_correct_values(self):
        """
        Verify serializer returns the stored values.
        """

        serializer = PackingItemSerializer(
            self.item,
        )

        self.assertEqual(
            serializer.data["category"],
            PackingCategory.CLOTHING,
        )

        self.assertEqual(
            serializer.data["item"],
            "Rain Jacket",
        )

        self.assertEqual(
            serializer.data["quantity"],
            1,
        )

        self.assertEqual(
            serializer.data["reason"],
            "Expected rain during the trip.",
        )

        self.assertTrue(
            serializer.data["is_ai_generated"],
        )

    def test_serializer_is_read_only(self):
        """
        Verify every serializer field is read-only.
        """

        serializer = PackingItemSerializer()

        for field in serializer.fields.values():

            self.assertTrue(
                field.read_only,
            )