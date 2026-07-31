"""
Tests for the Accounts admin configuration.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserAdminTests(TestCase):
    """
    Tests for the custom User admin.
    """

    def test_user_model_registered(self):
        """
        The custom User model should be registered with the admin site.
        """

        self.assertIn(
            User,
            admin.site._registry,
        )

    def test_admin_class_registered(self):
        """
        The registered admin class should exist.
        """

        admin_instance = admin.site._registry[User]

        self.assertIsNotNone(
            admin_instance,
        )

    def test_list_display_contains_email(self):
        """
        Email should be displayed in the admin list.
        """

        admin_instance = admin.site._registry[User]

        self.assertIn(
            "email",
            admin_instance.list_display,
        )

    def test_search_fields_contains_email(self):
        """
        Email should be searchable.
        """

        admin_instance = admin.site._registry[User]

        self.assertIn(
            "email",
            admin_instance.search_fields,
        )