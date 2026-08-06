"""
Unit tests for the Conversation Memory Manager.
"""

from __future__ import annotations

from unittest.mock import Mock

from ai.memory.conversation_manager import ConversationManager
from ai.memory.conversation_memory import ConversationMemory
from ai.memory.message import ConversationMessage

from datetime import datetime

from ai import memory


class TestConversationManagerInitialization:
    """
    Verify ConversationManager initialization.
    """

    def test_uses_injected_summarizer(self) -> None:
        summarizer = Mock()

        manager = ConversationManager(
            summarizer=summarizer,
        )

        assert manager._summarizer is summarizer


class TestConversationManager:
    """
    Verify conversation optimization behaviour.
    """

    def setup_method(self) -> None:
        self.summarizer = Mock()

        self.summarizer.summarize.return_value = (
            "Conversation Summary"
        )

        self.manager = ConversationManager(
            summarizer=self.summarizer,
        )

    def test_returns_same_memory_when_no_summary_needed(
        self,
    ) -> None:
        """
        Memory below the token limit should not be summarized.
        """

        memory = ConversationMemory(
            max_tokens=1000,
        )

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Hello",
                timestamp=datetime.utcnow(),
            )
        )

        result = self.manager.optimize_memory(
            memory,
        )

        assert result is memory

        self.summarizer.summarize.assert_not_called()

    def test_calls_summarizer_when_needed(
        self,
    ) -> None:
        """
        Oversized memory should trigger summarization.
        """

        memory = ConversationMemory(
            max_tokens=1,
        )

        for i in range(12):
            memory.add_message(
                ConversationMessage(
                    role="user",
                    content=f"Message {i}",
                    timestamp=datetime.utcnow(),
                )
            )

        self.manager.optimize_memory(
            memory,
        )

        self.summarizer.summarize.assert_called_once()

    def test_summary_is_saved(
        self,
    ) -> None:
        """
        The generated summary should be stored on the memory object.
        """

        memory = ConversationMemory(
        max_tokens=1,
        )

        for i in range(12):
            memory.add_message(
                ConversationMessage(
                    role="user",
                    content=f"Message {i}",
                    timestamp=datetime.utcnow(),
                )
            )

        self.manager.optimize_memory(
        memory,
    )

        assert memory.summary == "Conversation Summary"

    def test_recent_messages_are_preserved(
        self,
    ) -> None:
        """
        The configured number of recent messages should remain.
        """

        memory = ConversationMemory(
            max_tokens=1,
        )

        for i in range(12):
            memory.add_message(
                ConversationMessage(
                    role="user",
                    content=f"Message {i}",
                    timestamp=datetime.utcnow(),
                )
            )

        self.manager.optimize_memory(
            memory,
        )

        expected = [
            f"Message {i}"
            for i in range(6, 12)
        ]

        actual = [
            message.content
            for message in memory.messages
        ]

        assert actual == expected

    def test_old_messages_are_removed(
        self,
    ) -> None:
        """
        Messages outside the preserved window should be removed.
        """

        memory = ConversationMemory(
            max_tokens=1,
        )

        for i in range(12):
            memory.add_message(
                ConversationMessage(
                    role="user",
                    content=f"Message {i}",
                    timestamp=datetime.utcnow(),
                )
            )

        self.manager.optimize_memory(
            memory,
        )

        contents = [
            message.content
            for message in memory.messages
        ]

        assert "Message 0" not in contents
        assert "Message 1" not in contents
        assert "Message 2" not in contents
        assert "Message 3" not in contents
        assert "Message 4" not in contents
        assert "Message 5" not in contents

    def test_returns_same_memory_instance(
        self,
    ) -> None:
        """
        optimize_memory should mutate the existing object.
        """

        memory = ConversationMemory(
            max_tokens=1,
        )

        for i in range(12):
            memory.add_message(
                ConversationMessage(
                    role="user",
                    content=f"Message {i}",
                    timestamp=datetime.utcnow(),
                )
            )

        result = self.manager.optimize_memory(
            memory,
        )

        assert result is memory