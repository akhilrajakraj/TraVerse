"""
Conversation Memory Manager.

Coordinates conversation history, token estimation and summarization
without introducing provider-specific logic into the memory model.
"""

from __future__ import annotations

from ai.memory.conversation_memory import ConversationMemory
from ai.memory.memory_summarizer import (
    MemorySummarizer,
    memory_summarizer,
)


class ConversationManager:
    """
    High-level orchestration for conversation memory.

    Responsibilities:

    - inspect memory size
    - trigger summarization
    - preserve recent messages
    - update ConversationMemory

    This class intentionally does NOT:

    - access Django models
    - persist memory
    - know about REST APIs
    - know about LangGraph
    """

    #: Number of most-recent messages preserved after summarization.
    RECENT_MESSAGE_COUNT = 6

    def __init__(
        self,
        *,
        summarizer: MemorySummarizer | None = None,
    ) -> None:
        self._summarizer = summarizer or memory_summarizer

    def optimize_memory(
        self,
        memory: ConversationMemory,
    ) -> ConversationMemory:
        """
        Optimize conversation history if it exceeds the configured
        token budget.
        """

        if not memory.needs_summarization:
            return memory

        transcript = memory.transcript()

        summary = self._summarizer.summarize(
            conversation=transcript,
        )

        recent_messages = (
            memory.messages[-self.RECENT_MESSAGE_COUNT :]
            if memory.messages
            else []
        )

        memory.replace_with_summary(summary)

        memory.messages.extend(recent_messages)

        return memory


conversation_manager = ConversationManager()