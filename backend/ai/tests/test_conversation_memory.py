from datetime import datetime

from ai.memory.conversation_memory import ConversationMemory
from ai.memory.message import ConversationMessage


class TestConversationMemory:
    """
    Unit tests for ConversationMemory.
    """

    def test_defaults(self) -> None:
        memory = ConversationMemory()

        assert memory.summary == ""
        assert memory.messages == []
        assert memory.max_tokens == 8000

    def test_add_message(self) -> None:
        memory = ConversationMemory()

        message = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=datetime.utcnow(),
        )

        memory.add_message(message)

        assert len(memory.messages) == 1
        assert memory.messages[0] is message

    def test_clear(self) -> None:
        memory = ConversationMemory(
            summary="Previous summary",
        )

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Hello",
                timestamp=datetime.utcnow(),
            )
        )

        memory.clear()

        assert memory.summary == ""
        assert memory.messages == []

    def test_replace_with_summary(self) -> None:
        memory = ConversationMemory()

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Hello",
                timestamp=datetime.utcnow(),
            )
        )

        memory.replace_with_summary(
            "Conversation Summary",
        )

        assert memory.summary == "Conversation Summary"
        assert memory.messages == []

    def test_replace_with_summary_strips_whitespace(self) -> None:
        memory = ConversationMemory()

        memory.replace_with_summary(
            "   Summary   ",
        )

        assert memory.summary == "Summary"

    def test_transcript_without_summary(self) -> None:
        memory = ConversationMemory()

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Hello",
                timestamp=datetime.utcnow(),
            )
        )

        memory.add_message(
            ConversationMessage(
                role="assistant",
                content="Hi there",
                timestamp=datetime.utcnow(),
            )
        )

        transcript = memory.transcript()

        assert transcript == (
            "User: Hello\n"
            "Assistant: Hi there"
        )

    def test_transcript_with_summary(self) -> None:
        memory = ConversationMemory(
            summary="Old conversation",
        )

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Continue",
                timestamp=datetime.utcnow(),
            )
        )

        transcript = memory.transcript()

        assert transcript == (
            "Conversation Summary:\n"
            "Old conversation\n\n"
            "User: Continue"
        )

    def test_needs_summarization_false(self) -> None:
        memory = ConversationMemory(
            max_tokens=1000,
        )

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Short message",
                timestamp=datetime.utcnow(),
            )
        )

        assert memory.needs_summarization is False

    def test_needs_summarization_true(self) -> None:
        memory = ConversationMemory(
            max_tokens=1,
        )

        memory.add_message(
            ConversationMessage(
                role="user",
                content="This message is intentionally long enough to exceed the configured token budget.",
                timestamp=datetime.utcnow(),
            )
        )

        assert memory.needs_summarization is True

    def test_total_tokens_includes_summary(self) -> None:
        memory = ConversationMemory(
            summary="Conversation Summary",
        )

        memory.add_message(
            ConversationMessage(
                role="user",
                content="Hello",
                timestamp=datetime.utcnow(),
            )
        )

        assert memory.total_tokens > 0