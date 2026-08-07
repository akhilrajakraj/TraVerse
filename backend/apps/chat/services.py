"""
Persistence services for the Chat application.

Architecture
------------
This module owns ONLY chat persistence.

Responsibilities
----------------
- Create chat sessions
- Retrieve active sessions
- Persist chat messages
- Retrieve ordered conversation history
- Deactivate sessions

This module intentionally DOES NOT:

- import anything from ai.*
- call Groq
- build prompts
- summarize conversations
- execute LangGraph

AI orchestration belongs exclusively to apps.ai_agents.
"""

from __future__ import annotations

from django.db import transaction

from apps.chat.models import (
    ChatMessage,
    ChatRole,
    ChatSession,
)
from apps.trips.models import Trip


class ChatService:
    """
    Persistence service for chat conversations.
    """

    # ==========================================================
    # SESSION MANAGEMENT
    # ==========================================================

    @staticmethod
    @transaction.atomic
    def create_session(
        *,
        trip: Trip,
        title: str = "Travel Assistant",
    ) -> ChatSession:
        """
        Create a new active chat session.

        Any existing active session for the trip is deactivated.
        """

        ChatSession.objects.filter(
            trip=trip,
            is_active=True,
        ).update(
            is_active=False,
        )

        return ChatSession.objects.create(
            trip=trip,
            title=title,
            is_active=True,
        )

    @staticmethod
    def get_active_session(
        *,
        trip: Trip,
    ) -> ChatSession | None:
        """
        Return the current active session.
        """

        return (
            ChatSession.objects.filter(
                trip=trip,
                is_active=True,
            )
            .select_related("trip")
            .first()
        )

    @staticmethod
    def get_or_create_active_session(
        *,
        trip: Trip,
    ) -> ChatSession:
        """
        Return the active session or create one.
        """

        session = ChatService.get_active_session(
            trip=trip,
        )

        if session is not None:
            return session

        return ChatService.create_session(
            trip=trip,
        )

    @staticmethod
    def deactivate_session(
        *,
        session: ChatSession,
    ) -> None:
        """
        Mark a session as inactive.
        """

        session.is_active = False

        session.save(
            update_fields=[
                "is_active",
            ],
        )

    # ==========================================================
    # MESSAGE MANAGEMENT
    # ==========================================================

    @staticmethod
    def add_user_message(
        *,
        session: ChatSession,
        content: str,
    ) -> ChatMessage:
        """
        Persist a user message.
        """

        return ChatService._create_message(
            session=session,
            role=ChatRole.USER,
            content=content,
        )

    @staticmethod
    def add_assistant_message(
        *,
        session: ChatSession,
        content: str,
    ) -> ChatMessage:
        """
        Persist an assistant message.
        """

        return ChatService._create_message(
            session=session,
            role=ChatRole.ASSISTANT,
            content=content,
        )

    @staticmethod
    def add_system_message(
        *,
        session: ChatSession,
        content: str,
    ) -> ChatMessage:
        """
        Persist a system message.
        """

        return ChatService._create_message(
            session=session,
            role=ChatRole.SYSTEM,
            content=content,
        )

    @staticmethod
    def get_history(
        *,
        session: ChatSession,
    ):
        """
        Return ordered conversation history.
        """

        return (
            session.messages
            .all()
            .order_by("created_at")
        )

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    @staticmethod
    def _create_message(
        *,
        session: ChatSession,
        role: str,
        content: str,
    ) -> ChatMessage:
        """
        Internal helper for creating chat messages.
        """

        return ChatMessage.objects.create(
            session=session,
            role=role,
            content=content.strip(),
        )