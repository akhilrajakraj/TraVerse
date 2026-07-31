"""
Tests for the Profiles admin configuration.
"""

from django.contrib import admin
from django.test import TestCase

from apps.profiles.models import Profile


class ProfileAdminTests(TestCase):
    """
    Tests for the Profile admin configuration.
    """

    def test_profile_model_registered(self):
        """
        The Profile model should be registered with the admin site.
        """

        self.assertIn(
            Profile,
            admin.site._registry,
        )

    def test_admin_class_registered(self):
        """
        The registered admin class should exist.
        """

        admin_instance = admin.site._registry[Profile]

        self.assertIsNotNone(
            admin_instance,
        )

    def test_list_display_configuration(self):
        """
        Verify list_display configuration.
        """

        admin_instance = admin.site._registry[Profile]

        self.assertIn(
            "user",
            admin_instance.list_display,
        )

        self.assertIn(
            "phone_number",
            admin_instance.list_display,
        )

        self.assertIn(
            "gender",
            admin_instance.list_display,
        )

    def test_search_fields_configuration(self):
        """
        Verify search_fields configuration.
        """

        admin_instance = admin.site._registry[Profile]

        self.assertIn(
            "user__email",
            admin_instance.search_fields,
        )

        self.assertIn(
            "phone_number",
            admin_instance.search_fields,
        )