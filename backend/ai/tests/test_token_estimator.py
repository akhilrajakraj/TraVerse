from datetime import datetime

import pytest

from ai.memory.message import ConversationMessage
from ai.memory.token_estimator import TokenEstimator


class TestTokenEstimator:
    """
    Unit tests for TokenEstimator.
    """

    def test_empty_string_returns_zero_tokens(self) -> None:
        assert TokenEstimator.estimate_text("") == 0

    def test_whitespace_returns_zero_tokens(self) -> None:
        assert TokenEstimator.estimate_text("     ") == 0

    def test_single_character_returns_one_token(self) -> None:
        assert TokenEstimator.estimate_text("a") == 1

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("abcd", 1),
            ("abcde", 2),
            ("abcdefgh", 2),
            ("abcdefghi", 3),
            ("Hello World", 3),
        ],
    )
    def test_estimate_text(
        self,
        text: str,
        expected: int,
    ) -> None:
        assert TokenEstimator.estimate_text(text) == expected

    def test_estimate_single_message(self) -> None:
        message = ConversationMessage(
            role="user",
            content="Hello World",
            timestamp=datetime.utcnow(),
        )

        assert (
            TokenEstimator.estimate_message(message)
            == TokenEstimator.estimate_text("Hello World")
        )

    def test_estimate_multiple_messages(self) -> None:
        messages = [
            ConversationMessage(
                role="user",
                content="Hello",
                timestamp=datetime.utcnow(),
            ),
            ConversationMessage(
                role="assistant",
                content="Hi there",
                timestamp=datetime.utcnow(),
            ),
        ]

        expected = (
            TokenEstimator.estimate_text("Hello")
            + TokenEstimator.estimate_text("Hi there")
        )

        assert (
            TokenEstimator.estimate_messages(messages)
            == expected
        )

    def test_empty_message_list(self) -> None:
        assert TokenEstimator.estimate_messages([]) == 0

    def test_token_estimation_is_deterministic(self) -> None:
        text = (
            "This sentence should always produce "
            "the same token estimate."
        )

        first = TokenEstimator.estimate_text(text)
        second = TokenEstimator.estimate_text(text)

        assert first == second

    def test_trimmed_text_produces_same_result(self) -> None:
        clean = TokenEstimator.estimate_text(
            "Hello World",
        )

        spaced = TokenEstimator.estimate_text(
            "   Hello World   ",
        )

        assert clean == spaced