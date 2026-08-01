"""
Admin tests for the Destinations application.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from apps.destinations.admin import DestinationAdmin
from apps.destinations.models import Destination


class DestinationAdminTests(TestCase):
    """
    Test suite for Destination admin configuration.
    """

    def setUp(self):
        self.site = AdminSite()

        self.admin = DestinationAdmin(
            Destination,
            self.site,
        )

    def test_list_display(self):
        """
        Verify the configured list display.
        """

        self.assertEqual(
            self.admin.list_display,
            (
                "name",
                "country",
                "city",
                "is_active",
                "created_at",
                "updated_at",
            ),
        )

    def test_search_fields(self):
        """
        Verify searchable fields.
        """

        self.assertEqual(
            self.admin.search_fields,
            (
                "name",
                "country",
                "city",
            ),
        )

    def test_list_filter(self):
        """
        Verify configured filters.
        """

        self.assertEqual(
            self.admin.list_filter,
            (
                "country",
                "is_active",
            ),
        )

    def test_readonly_fields(self):
        """
        Verify read-only infrastructure fields.
        """

        self.assertEqual(
            self.admin.readonly_fields,
            (
                "id",
                "created_at",
                "updated_at",
            ),
        )