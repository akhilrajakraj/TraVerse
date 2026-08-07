"""
Serializers for the Chat application.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.chat.models import (
    ChatMessage,
    ChatRole,
    ChatSession,
)


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serialize persisted chat messages.
    """

    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = ChatMessage

        fields = (
            "id",
            "role",
            "role_display",
            "content",
            "created_at",
        )

        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serialize chat sessions together with
    their ordered conversation history.
    """

    messages = ChatMessageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ChatSession

        fields = (
            "id",
            "title",
            "is_active",
            "created_at",
            "updated_at",
            "messages",
        )

        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    """
    Incoming user message.
    """

    message = serializers.CharField(
        max_length=4000,
        trim_whitespace=True,
    )

    def validate_message(
        self,
        value: str,
    ) -> str:
        """
        Reject empty messages.
        """

        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Message cannot be empty.",
            )

        return value


class ChatResponseSerializer(serializers.Serializer):
    """
    Outgoing assistant response.
    """

    session_id = serializers.UUIDField()

    assistant_message = serializers.CharField()

    created_at = serializers.DateTimeField()