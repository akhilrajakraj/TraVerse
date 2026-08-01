"""
Model tests for the Destinations application.
"""

import uuid

from django.test import TestCase

from apps.destinations.models import Destination


class DestinationModelTests(TestCase):
    """
    Test suite for the Destination model.
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

    def test_destination_creation(self):
        """
        Destination should be created successfully.
        """

        self.assertEqual(
            Destination.objects.count(),
            1,
        )

    def test_uuid_primary_key(self):
        """
        Destination should use UUID primary keys.
        """

        self.assertIsInstance(
            self.destination.id,
            uuid.UUID,
        )

    def test_string_representation(self):
        """
        __str__ should return the destination name.
        """

        self.assertEqual(
            str(self.destination),
            "Tokyo",
        )

    def test_default_is_active(self):
        """
        Destinations should be active by default.
        """

        self.assertTrue(
            self.destination.is_active,
        )

    def test_ordering(self):
        """
        Destinations should respect Meta ordering.
        """

        Destination.objects.create(
            name="Kyoto",
            country="Japan",
            city="Kyoto",
            latitude=35.0116,
            longitude=135.7681,
        )

        destinations = list(
            Destination.objects.all()
        )

        self.assertEqual(
            destinations[0].city,
            "Kyoto",
        )

        self.assertEqual(
            destinations[1].city,
            "Tokyo",
        )

    def test_timestamp_fields_exist(self):
        """
        Timestamp fields should be populated.
        """

        self.assertIsNotNone(
            self.destination.created_at,
        )

        self.assertIsNotNone(
            self.destination.updated_at,
        )