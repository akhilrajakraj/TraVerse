"""
Utilities for estimating LLM token usage.

The estimator intentionally provides a lightweight approximation rather
than relying on a provider-specific tokenizer.
"""

from __future__ import annotations

from ai.memory.message import ConversationMessage


class TokenEstimator:
    """
    Estimate token counts for conversation messages.

    The implementation intentionally uses a simple heuristic
    (roughly four characters per token) to remain deterministic,
    offline, and independent of any specific LLM provider.
    """

    CHARS_PER_TOKEN = 4

    @classmethod
    def estimate_text(cls, text: str) -> int:
        """
        Estimate the number of tokens contained in a text string.
        """

        text = text.strip()

        if not text:
            return 0

        return max(
            1,
            (len(text) + cls.CHARS_PER_TOKEN - 1)
            // cls.CHARS_PER_TOKEN,
        )

    @classmethod
    def estimate_message(
        cls,
        message: ConversationMessage,
    ) -> int:
        """
        Estimate the token count for a conversation message.
        """

        return cls.estimate_text(message.content)

    @classmethod
    def estimate_messages(
        cls,
        messages: list[ConversationMessage],
    ) -> int:
        """
        Estimate the total token count across multiple messages.
        """

        return sum(
            cls.estimate_message(message)
            for message in messages
        )


token_estimator = TokenEstimator()