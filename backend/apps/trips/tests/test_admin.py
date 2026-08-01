"""
Admin tests for the Trips application.
"""

from datetime import date, timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.trips.admin import TripAdmin
from apps.trips.models import Trip


User = get_user_model()


class TripAdminTests(TestCase):
    """
    Test suite for Trip admin configuration.
    """

    def test_model_is_registered(self):
        """
        Verify Trip is registered with Django Admin.
        """

        self.assertIn(
            Trip,
            admin.site._registry,
        )

    def test_admin_class(self):
        """
        Verify the registered admin class.
        """

        self.assertIsInstance(
            admin.site._registry[Trip],
            TripAdmin,
        )

    def test_list_display(self):
        """
        Verify configured list display fields.
        """

        trip_admin = admin.site._registry[
            Trip
        ]

        self.assertEqual(
            trip_admin.list_display,
            (
                "title",
                "user",
                "status",
                "traveler_count",
                "start_date",
                "end_date",
                "created_at",
            ),
        )

    def test_readonly_fields(self):
        """
        Verify infrastructure fields remain read-only.
        """

        trip_admin = admin.site._registry[
            Trip
        ]

        self.assertEqual(
            trip_admin.readonly_fields,
            (
                "id",
                "computed_budget_total",
                "created_at",
                "updated_at",
            ),
        )