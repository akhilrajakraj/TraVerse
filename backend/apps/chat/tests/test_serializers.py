"""
Unit tests for chat serializers.
"""

from __future__ import annotations

from datetime import date

from django.test import TestCase

from apps.accounts.models import User
from apps.chat.models import (
    ChatMessage,
    ChatRole,
)
from apps.chat.serializers import (
    ChatMessageSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatSessionSerializer,
)
from apps.chat.services import ChatService
from apps.trips.models import Trip


class ChatMessageSerializerTests(TestCase):
    """
    Verify ChatMessageSerializer.
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

        self.message = ChatService.add_user_message(
            session=self.session,
            content="Hello TraVerse",
        )

    def test_contains_expected_fields(self) -> None:

        serializer = ChatMessageSerializer(
            self.message,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "role",
                "role_display",
                "content",
                "created_at",
            },
        )

    def test_serializes_content(self) -> None:

        serializer = ChatMessageSerializer(
            self.message,
        )

        self.assertEqual(
            serializer.data["content"],
            "Hello TraVerse",
        )

    def test_serializes_role(self) -> None:

        serializer = ChatMessageSerializer(
            self.message,
        )

        self.assertEqual(
            serializer.data["role"],
            ChatRole.USER,
        )


class ChatSessionSerializerTests(TestCase):
    """
    Verify ChatSessionSerializer.
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

        ChatService.add_user_message(
            session=self.session,
            content="Hello",
        )

        ChatService.add_assistant_message(
            session=self.session,
            content="Hi!",
        )

    def test_contains_messages(self) -> None:

        serializer = ChatSessionSerializer(
            self.session,
        )

        self.assertEqual(
            len(serializer.data["messages"]),
            2,
        )

    def test_contains_session_fields(self) -> None:

        serializer = ChatSessionSerializer(
            self.session,
        )

        self.assertEqual(
            set(serializer.data.keys()),
            {
                "id",
                "title",
                "is_active",
                "created_at",
                "updated_at",
                "messages",
            },
        )


class ChatRequestSerializerTests(TestCase):
    """
    Verify request validation.
    """

    def test_accepts_valid_message(self) -> None:

        serializer = ChatRequestSerializer(
            data={
                "message": "Hello",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
        )

    def test_rejects_blank_message(self) -> None:

        serializer = ChatRequestSerializer(
            data={
                "message": "    ",
            },
        )

        self.assertFalse(
            serializer.is_valid(),
        )

        self.assertIn(
            "message",
            serializer.errors,
        )

    def test_trims_whitespace(self) -> None:

        serializer = ChatRequestSerializer(
            data={
                "message": "   Hello   ",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
        )

        self.assertEqual(
            serializer.validated_data["message"],
            "Hello",
        )


class ChatResponseSerializerTests(TestCase):
    """
    Verify response serializer.
    """

    def test_valid_response(self) -> None:

        session_id = (
            "12345678-1234-5678-1234-567812345678"
        )

        serializer = ChatResponseSerializer(
            data={
                "session_id": session_id,
                "assistant_message": "Welcome!",
                "created_at": "2026-01-01T10:00:00Z",
            },
        )

        self.assertTrue(
            serializer.is_valid(),
        )