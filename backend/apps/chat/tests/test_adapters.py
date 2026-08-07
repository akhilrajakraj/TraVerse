"""
Unit tests for the ConversationMemoryAdapter.
"""

from __future__ import annotations

from datetime import date

from django.test import TestCase

from ai.memory.conversation_memory import ConversationMemory

from apps.accounts.models import User
from apps.chat.adapters import ConversationMemoryAdapter
from apps.chat.models import ChatRole
from apps.chat.services import ChatService
from apps.trips.models import Trip


class ConversationMemoryAdapterTests(TestCase):
    """
    Verify database chat history is converted into
    AI conversation memory.
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

    def test_returns_conversation_memory(self) -> None:
        """
        Adapter should return ConversationMemory.
        """

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertIsInstance(
            memory,
            ConversationMemory,
        )

    def test_empty_session_returns_empty_memory(self) -> None:
        """
        Empty sessions should produce empty memory.
        """

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertEqual(
            len(memory.messages),
            0,
        )

    def test_loads_all_messages(self) -> None:
        """
        Every persisted message should be loaded.
        """

        ChatService.add_user_message(
            session=self.session,
            content="Hello",
        )

        ChatService.add_assistant_message(
            session=self.session,
            content="Hi!",
        )

        ChatService.add_system_message(
            session=self.session,
            content="Summary",
        )

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertEqual(
            len(memory.messages),
            3,
        )

    def test_preserves_order(self) -> None:
        """
        Messages should remain chronological.
        """

        ChatService.add_user_message(
            session=self.session,
            content="First",
        )

        ChatService.add_assistant_message(
            session=self.session,
            content="Second",
        )

        ChatService.add_system_message(
            session=self.session,
            content="Third",
        )

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertEqual(
            [m.content for m in memory.messages],
            [
                "First",
                "Second",
                "Third",
            ],
        )

    def test_preserves_roles(self) -> None:
        """
        Roles should remain unchanged.
        """

        ChatService.add_user_message(
            session=self.session,
            content="Hello",
        )

        ChatService.add_assistant_message(
            session=self.session,
            content="Hi",
        )

        ChatService.add_system_message(
            session=self.session,
            content="Summary",
        )

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertEqual(
            [m.role for m in memory.messages],
            [
                ChatRole.USER,
                ChatRole.ASSISTANT,
                ChatRole.SYSTEM,
            ],
        )

    def test_preserves_content(self) -> None:
        """
        Message content should be unchanged.
        """

        ChatService.add_user_message(
            session=self.session,
            content="Where should I stay?",
        )

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertEqual(
            memory.messages[0].content,
            "Where should I stay?",
        )

    def test_preserves_timestamps(self) -> None:
        """
        Original timestamps should be preserved.
        """

        stored = ChatService.add_user_message(
            session=self.session,
            content="Timestamp",
        )

        memory = ConversationMemoryAdapter.build_memory(
            session=self.session,
        )

        self.assertEqual(
            memory.messages[0].timestamp,
            stored.created_at,
        )