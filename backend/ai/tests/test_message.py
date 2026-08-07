from datetime import datetime

import pytest

from ai.memory.message import ConversationMessage


class TestConversationMessage:
    """
    Unit tests for ConversationMessage.
    """

    def test_create_message(self) -> None:
        timestamp = datetime.utcnow()

        message = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=timestamp,
        )

        assert message.role == "user"
        assert message.content == "Hello"
        assert message.timestamp is timestamp
        assert message.token_count is None

    def test_create_message_with_token_count(self) -> None:
        message = ConversationMessage(
            role="assistant",
            content="Hi!",
            timestamp=datetime.utcnow(),
            token_count=42,
        )

        assert message.token_count == 42

    @pytest.mark.parametrize(
        "role",
        [
            "system",
            "user",
            "assistant",
            "tool",
        ],
    )
    def test_all_roles_are_supported(
        self,
        role: str,
    ) -> None:
        message = ConversationMessage(
            role=role,
            content="Message",
            timestamp=datetime.utcnow(),
        )

        assert message.role == role

    def test_is_immutable(self) -> None:
        message = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=datetime.utcnow(),
        )

        with pytest.raises((AttributeError, TypeError)):
            message.content = "Changed"

    def test_messages_with_same_values_are_equal(self) -> None:
        timestamp = datetime.utcnow()

        first = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=timestamp,
        )

        second = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=timestamp,
        )

        assert first == second

    def test_slots_are_enabled(self) -> None:
        message = ConversationMessage(
            role="assistant",
            content="Hello",
            timestamp=datetime.utcnow(),
        )

        with pytest.raises((AttributeError, TypeError)):
            message.new_attribute = "not allowed"