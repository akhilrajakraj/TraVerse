"""
Conversation memory manager.

Maintains conversational history independently of Django and LLM providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.memory.message import ConversationMessage
from ai.memory.token_estimator import token_estimator


@dataclass(slots=True)
class ConversationMemory:
    """
    Stores conversational history and provides token-aware utilities.

    This class intentionally contains no provider-specific logic.
    """

    max_tokens: int = 8_000

    summary: str = ""

    messages: list[ConversationMessage] = field(default_factory=list)

    def add_message(
        self,
        message: ConversationMessage,
    ) -> None:
        """
        Append a conversation message.
        """

        self.messages.append(message)

    def clear(self) -> None:
        """
        Remove all conversation state.
        """

        self.summary = ""
        self.messages.clear()

    @property
    def total_tokens(self) -> int:
        """
        Estimated tokens currently stored.
        """

        total = token_estimator.estimate_messages(
            self.messages,
        )

        if self.summary:
            total += token_estimator.estimate_text(
                self.summary,
            )

        return total

    @property
    def needs_summarization(self) -> bool:
        """
        Determine whether the memory exceeds the configured limit.
        """

        return self.total_tokens > self.max_tokens

    def transcript(self) -> str:
        """
        Build a plain-text transcript.
        """

        lines: list[str] = []

        if self.summary:

            lines.append("Conversation Summary:")
            lines.append(self.summary)
            lines.append("")

        for message in self.messages:

            lines.append(
                f"{message.role.title()}: {message.content}"
            )

        return "\n".join(lines)

    def replace_with_summary(
        self,
        summary: str,
    ) -> None:
        """
        Replace detailed history with a condensed summary.
        """

        self.summary = summary.strip()

        self.messages.clear()


conversation_memory = ConversationMemory()