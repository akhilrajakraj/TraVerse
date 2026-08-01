"""
Serializer tests for the Destinations application.
"""

from django.test import TestCase

from apps.destinations.models import Destination
from apps.destinations.serializers import DestinationSerializer


class DestinationSerializerTests(TestCase):
    """
    Test suite for the Destination serializer.
    """

    def setUp(self):
        self.destination = Destination.objects.create(
            name="Tokyo",
            country="Japan",
            city="Tokyo",
            latitude=35.6762,
            longitude=139.6503,
            image_url="https://example.com/tokyo.jpg",
        )

    def test_serializer_contains_expected_fields(self):
        """
        Serializer should expose the expected fields.
        """

        serializer = DestinationSerializer(
            self.destination,
        )

        expected_fields = {
            "id",
            "name",
            "country",
            "city",
            "latitude",
            "longitude",
            "image_url",
            "is_active",
            "created_at",
            "updated_at",
        }

        self.assertEqual(
            set(serializer.data.keys()),
            expected_fields,
        )

    def test_serializer_returns_correct_values(self):
        """
        Serializer should correctly serialize destination data.
        """

        serializer = DestinationSerializer(
            self.destination,
        )

        self.assertEqual(
            serializer.data["name"],
            "Tokyo",
        )

        self.assertEqual(
            serializer.data["country"],
            "Japan",
        )

        self.assertEqual(
            serializer.data["city"],
            "Tokyo",
        )

    def test_read_only_fields(self):
        """
        Infrastructure fields should remain read-only.
        """

        serializer = DestinationSerializer()

        self.assertEqual(
            set(serializer.Meta.read_only_fields),
            {
                "id",
                "created_at",
                "updated_at",
            },
        )