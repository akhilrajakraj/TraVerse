"""
Tests for the Chat Django admin configuration.
"""

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from apps.chat.admin import (
    ChatMessageAdmin,
    ChatSessionAdmin,
)
from apps.chat.models import (
    ChatMessage,
    ChatSession,
)


class ChatSessionAdminTests(TestCase):
    """
    Verify ChatSession admin configuration.
    """

    def setUp(self) -> None:
        self.site = AdminSite()

        self.admin = ChatSessionAdmin(
            ChatSession,
            self.site,
        )

    def test_model_is_registered(self) -> None:
        """
        Verify ChatSession is registered.
        """

        assert self.site.is_registered(
            ChatSession,
        ) is False

    def test_list_display(self) -> None:
        """
        Verify configured list display.
        """

        assert self.admin.list_display == (
            "title",
            "trip",
            "is_active",
            "created_at",
        )

    def test_readonly_fields(self) -> None:
        """
        Infrastructure fields remain read-only.
        """

        assert self.admin.readonly_fields == (
            "id",
            "created_at",
            "updated_at",
        )

    def test_list_filter(self) -> None:
        """
        Verify configured filters.
        """

        assert self.admin.list_filter == (
            "is_active",
            "created_at",
        )

    def test_search_fields(self) -> None:
        """
        Verify searchable fields.
        """

        assert self.admin.search_fields == (
            "title",
            "trip__title",
        )

    def test_list_select_related(self) -> None:
        """
        Verify select_related optimization.
        """

        assert self.admin.list_select_related == (
            "trip",
        )

    def test_ordering(self) -> None:
        """
        Verify default ordering.
        """

        assert self.admin.ordering == (
            "-created_at",
        )


class ChatMessageAdminTests(TestCase):
    """
    Verify ChatMessage admin configuration.
    """

    def setUp(self) -> None:
        self.site = AdminSite()

        self.admin = ChatMessageAdmin(
            ChatMessage,
            self.site,
        )

    def test_list_display(self) -> None:
        """
        Verify configured list display.
        """

        assert self.admin.list_display == (
            "session",
            "role",
            "short_content",
            "created_at",
        )

    def test_readonly_fields(self) -> None:
        """
        Infrastructure fields remain read-only.
        """

        assert self.admin.readonly_fields == (
            "id",
            "created_at",
            "updated_at",
        )

    def test_list_filter(self) -> None:
        """
        Verify configured filters.
        """

        assert self.admin.list_filter == (
            "role",
            "created_at",
        )

    def test_search_fields(self) -> None:
        """
        Verify searchable fields.
        """

        assert self.admin.search_fields == (
            "content",
            "session__title",
            "session__trip__title",
        )

    def test_list_select_related(self) -> None:
        """
        Verify select_related optimization.
        """

        assert self.admin.list_select_related == (
            "session",
            "session__trip",
        )

    def test_ordering(self) -> None:
        """
        Verify default ordering.
        """

        assert self.admin.ordering == (
            "created_at",
        )