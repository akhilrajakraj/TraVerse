"""
Persistent chat models for AI travel conversations.

These models provide the persistence layer for conversational AI.

Architecture Responsibilities
-----------------------------

ChatSession
    Represents one conversation associated with a Trip.

ChatMessage
    Stores every user and assistant message exchanged during the
    conversation.

AI processing, memory summarization, prompt construction, and LLM
interaction are intentionally handled by the ai/ package and
apps.ai_agents service layer.
"""

from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


# =====================================================================
# MESSAGE ROLE
# =====================================================================


class ChatRole(models.TextChoices):
    """
    Supported chat participant roles.
    """

    USER = "user", "User"

    ASSISTANT = "assistant", "Assistant"

    SYSTEM = "system", "System"


# =====================================================================
# CHAT SESSION
# =====================================================================


class ChatSession(
    UUIDPrimaryKeyModel,
    TimeStampedModel,
):
    """
    Persistent conversation attached to a Trip.

    A Trip may contain multiple chat sessions over its lifetime,
    although typically only one session is active.
    """

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )

    title = models.CharField(
        max_length=200,
        default="Travel Assistant",
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "Chat Session"

        verbose_name_plural = "Chat Sessions"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "trip",
                    "is_active",
                ],
                name="chat_session_trip_active_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.trip.title} - {self.title}"
        )


# =====================================================================
# CHAT MESSAGE
# =====================================================================


class ChatMessage(
    UUIDPrimaryKeyModel,
    TimeStampedModel,
):
    """
    Individual message within a chat session.
    """

    session = models.ForeignKey(
        "chat.ChatSession",
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ChatRole.choices,
    )

    content = models.TextField()

    class Meta:
        verbose_name = "Chat Message"

        verbose_name_plural = "Chat Messages"

        ordering = [
            "created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "session",
                    "created_at",
                ],
                name="chat_mess_sess_created_idx",
            ),
            models.Index(
                fields=[
                    "session",
                    "role",
                ],
                name="chat_message_session_role_idx",
            ),
        ]

    def __str__(self) -> str:
        preview = self.content.strip().replace("\n", " ")

        if len(preview) > 50:
            preview = preview[:47] + "..."

        return (
            f"{self.get_role_display()}: {preview}"
        )