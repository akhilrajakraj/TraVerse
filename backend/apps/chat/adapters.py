"""
Adapters between Django chat models and standalone AI memory objects.
"""

from __future__ import annotations

from ai.memory.conversation_memory import ConversationMemory
from ai.memory.message import ConversationMessage

from apps.chat.models import ChatSession


class ConversationMemoryAdapter:
    """
    Builds AI conversation memory from persisted chat history.
    """

    @staticmethod
    def build_memory(
        *,
        session: ChatSession,
        max_tokens: int = 8_000,
    ) -> ConversationMemory:
        """
        Convert database chat messages into AI memory.
        """

        memory = ConversationMemory(
            max_tokens=max_tokens,
        )

        messages = (
            session.messages
            .order_by("created_at")
            .only(
                "role",
                "content",
                "created_at",
            )
        )

        for message in messages:
            memory.add_message(
                ConversationMessage(
                    role=message.role,
                    content=message.content,
                    timestamp=message.created_at,
                )
            )

        return memory
    
conversation_memory_adapter = ConversationMemoryAdapter()