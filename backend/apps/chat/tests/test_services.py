"""
Unit tests for the ChatService.
"""

from __future__ import annotations

from django.test import TestCase

from apps.accounts.models import User
from apps.chat.models import ChatRole
from apps.chat.services import ChatService
from apps.trips.models import Trip

from datetime import date


class ChatServiceSessionTests(TestCase):
    """
    Verify session management.
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Adventure",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 20),
        )

    def test_create_session(self) -> None:
        """
        A new session should be active.
        """

        session = ChatService.create_session(
            trip=self.trip,
        )

        self.assertTrue(session.is_active)

        self.assertEqual(
            session.trip,
            self.trip,
        )

    def test_only_one_active_session(self) -> None:
        """
        Creating another session should deactivate
        the previous one.
        """

        first = ChatService.create_session(
            trip=self.trip,
        )

        second = ChatService.create_session(
            trip=self.trip,
        )

        first.refresh_from_db()

        self.assertFalse(first.is_active)

        self.assertTrue(second.is_active)

    def test_get_active_session(self) -> None:
        """
        Should return the active session.
        """

        session = ChatService.create_session(
            trip=self.trip,
        )

        active = ChatService.get_active_session(
            trip=self.trip,
        )

        self.assertEqual(
            active,
            session,
        )

    def test_get_or_create_returns_existing(self) -> None:
        """
        Existing session should be reused.
        """

        session = ChatService.create_session(
            trip=self.trip,
        )

        returned = ChatService.get_or_create_active_session(
            trip=self.trip,
        )

        self.assertEqual(
            returned.id,
            session.id,
        )

    def test_get_or_create_creates_session(self) -> None:
        """
        A session should be created when missing.
        """

        session = ChatService.get_or_create_active_session(
            trip=self.trip,
        )

        self.assertIsNotNone(session)

        self.assertTrue(session.is_active)

    def test_deactivate_session(self) -> None:
        """
        Session becomes inactive.
        """

        session = ChatService.create_session(
            trip=self.trip,
        )

        ChatService.deactivate_session(
            session=session,
        )

        session.refresh_from_db()

        self.assertFalse(session.is_active)


class ChatServiceMessageTests(TestCase):
    """
    Verify message persistence.
    """

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Adventure",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 20),
        )

        self.session = ChatService.create_session(
            trip=self.trip,
        )

    def test_add_user_message(self) -> None:
        """
        User messages should be stored.
        """

        message = ChatService.add_user_message(
            session=self.session,
            content="Hello",
        )

        self.assertEqual(
            message.role,
            ChatRole.USER,
        )

        self.assertEqual(
            message.content,
            "Hello",
        )

    def test_add_assistant_message(self) -> None:
        """
        Assistant messages should be stored.
        """

        message = ChatService.add_assistant_message(
            session=self.session,
            content="Hi there",
        )

        self.assertEqual(
            message.role,
            ChatRole.ASSISTANT,
        )

    def test_add_system_message(self) -> None:
        """
        System messages should be stored.
        """

        message = ChatService.add_system_message(
            session=self.session,
            content="Summary",
        )

        self.assertEqual(
            message.role,
            ChatRole.SYSTEM,
        )

    def test_history_returns_messages_in_order(self) -> None:
        """
        Conversation history should be chronological.
        """

        ChatService.add_user_message(
            session=self.session,
            content="First",
        )

        ChatService.add_assistant_message(
            session=self.session,
            content="Second",
        )

        history = list(
            ChatService.get_history(
                session=self.session,
            )
        )

        self.assertEqual(
            history[0].content,
            "First",
        )

        self.assertEqual(
            history[1].content,
            "Second",
        )

    def test_content_is_trimmed(self) -> None:
        """
        Whitespace should be stripped.
        """

        message = ChatService.add_user_message(
            session=self.session,
            content="   Hello World   ",
        )

        self.assertEqual(
            message.content,
            "Hello World",
        )