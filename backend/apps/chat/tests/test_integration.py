"""
End-to-end integration tests for the Chat application.

These tests verify the complete request pipeline:

HTTP Request
    ↓
APIView
    ↓
Serializer
    ↓
generate_chat_reply()
    ↓
ChatService
    ↓
Database
    ↓
HTTP Response
"""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.chat.models import (
    ChatMessage,
    ChatRole,
    ChatSession,
)
from apps.trips.models import Trip

from ai.exceptions import LLMCallFailed


class ChatIntegrationTests(APITestCase):
    """
    End-to-end integration tests.
    """

    def setUp(self) -> None:

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password123",
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
        )

        self.trip = Trip.objects.create(
            user=self.user,
            title="Japan Adventure",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 20),
        )

        self.other_trip = Trip.objects.create(
            user=self.other_user,
            title="Paris Adventure",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
        )

        self.url = reverse(
            "chat:chat",
            kwargs={
                "trip_id": self.trip.id,
            },
        )

        self.client.force_authenticate(
            self.user,
        )
        
    @patch("apps.ai_agents.services.ChatAgent")
    def test_complete_chat_pipeline(
        self,
        mock_chat_agent,
    ) -> None:
        """
        Verify the complete request pipeline executes while
        mocking only the LLM.
        """

        mock_chat_agent.return_value.reply.return_value = (
            "Welcome to Japan!"
        )

        response = self.client.post(
            self.url,
            {
                "message": "Plan my trip",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["assistant_message"],
            "Welcome to Japan!",
        )

        session = ChatSession.objects.get(
            trip=self.trip,
        )

        self.assertEqual(
            session.messages.count(),
            2,
        )

        messages = list(
            session.messages.order_by(
                "created_at",
            )
        )

        self.assertEqual(
            messages[0].role,
            ChatRole.USER,
        )

        self.assertEqual(
            messages[0].content,
            "Plan my trip",
        )

        self.assertEqual(
            messages[1].role,
            ChatRole.ASSISTANT,
        )

        self.assertEqual(
            messages[1].content,
            "Welcome to Japan!",
        )

        mock_chat_agent.return_value.reply.assert_called_once()
        
    @patch("apps.ai_agents.services.ChatAgent")
    def test_reuses_existing_session(
        self,
        mock_chat_agent,
    ) -> None:
        """
        Multiple requests should reuse the same active session.
        """

        mock_chat_agent.return_value.reply.return_value = (
            "Assistant Reply"
        )

        self.client.post(
            self.url,
            {
                "message": "Hello",
            },
            format="json",
        )

        first_session = ChatSession.objects.get(
            trip=self.trip,
        )

        self.client.post(
            self.url,
            {
                "message": "Tell me more",
            },
            format="json",
        )

        self.assertEqual(
            ChatSession.objects.filter(
                trip=self.trip,
            ).count(),
            1,
        )

        second_session = ChatSession.objects.get(
            trip=self.trip,
        )

        self.assertEqual(
            first_session.id,
            second_session.id,
        )

        self.assertEqual(
            second_session.messages.count(),
            4,
        )
        
    @patch("apps.ai_agents.services.ChatAgent")
    def test_history_is_persisted(
        self,
        mock_chat_agent,
    ) -> None:
        """
        Every request should append both the user message
        and the assistant reply to the conversation history.
        """

        mock_chat_agent.return_value.reply.side_effect = [
            "Hello!",
            "Let's plan your trip.",
        ]

        self.client.post(
            self.url,
            {
                "message": "Hi",
            },
            format="json",
        )

        self.client.post(
            self.url,
            {
                "message": "Plan my itinerary",
            },
            format="json",
        )

        session = ChatSession.objects.get(
            trip=self.trip,
        )

        messages = list(
            session.messages.order_by(
                "created_at",
            )
        )

        self.assertEqual(
            len(messages),
            4,
        )

        self.assertEqual(
            messages[0].role,
            ChatRole.USER,
        )

        self.assertEqual(
            messages[0].content,
            "Hi",
        )

        self.assertEqual(
            messages[1].role,
            ChatRole.ASSISTANT,
        )

        self.assertEqual(
            messages[1].content,
            "Hello!",
        )

        self.assertEqual(
            messages[2].role,
            ChatRole.USER,
        )

        self.assertEqual(
            messages[2].content,
            "Plan my itinerary",
        )

        self.assertEqual(
            messages[3].role,
            ChatRole.ASSISTANT,
        )

        self.assertEqual(
            messages[3].content,
            "Let's plan your trip.",
        )
        
    def test_other_user_cannot_access_trip(
        self,
    ) -> None:
        """
        Users must not be able to chat on trips they do not own.
        """

        url = reverse(
            "chat:chat",
            kwargs={
                "trip_id": self.other_trip.id,
            },
        )

        response = self.client.post(
            url,
            {
                "message": "Hello",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            ChatSession.objects.filter(
                trip=self.other_trip,
            ).exists(),
        )

        self.assertEqual(
            ChatMessage.objects.count(),
            0,
        )
        
    @patch("apps.ai_agents.services.ChatAgent")
    def test_llm_failure_preserves_user_message(
        self,
        mock_chat_agent,
    ) -> None:
        """
        Even if the LLM fails, the user's message should
        still be persisted because it was stored before
        ChatAgent execution.
        """

        mock_chat_agent.return_value.reply.side_effect = (
            LLMCallFailed("LLM unavailable")
        )

        with self.assertRaises(LLMCallFailed):
            self.client.post(
                self.url,
                {
                    "message": "Plan my trip",
                },
                format="json",
            )

        session = ChatSession.objects.get(
            trip=self.trip,
        )

        messages = list(
            session.messages.order_by(
                "created_at",
            )
        )

        self.assertEqual(
            len(messages),
            1,
        )

        self.assertEqual(
            messages[0].role,
            ChatRole.USER,
        )

        self.assertEqual(
            messages[0].content,
            "Plan my trip",
        )
        
    def test_blank_message_returns_400(
        self,
    ) -> None:
        """
        Blank messages should fail serializer validation.
        """

        response = self.client.post(
            self.url,
            {
                "message": "     ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "message",
            response.data["errors"],
        )

        self.assertEqual(
            ChatSession.objects.count(),
            0,
        )

        self.assertEqual(
            ChatMessage.objects.count(),
            0,
        )
        
    