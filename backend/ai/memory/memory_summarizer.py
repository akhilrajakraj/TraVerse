"""
Conversation Memory Summarizer.

Coordinates prompt generation and LLM execution for producing a compact
conversation summary.

This module intentionally remains independent of Django, LangGraph,
database models and REST APIs.
"""

from __future__ import annotations

from ai.clients.groq_client import GroqClient
from ai.prompts.memory_summarizer_v1 import (
    MemorySummarizerPromptV1,
    memory_summarizer_prompt_v1,
)


class MemorySummarizer:
    """
    Enterprise Conversation Memory Summarizer.

    Responsible only for coordinating prompt generation and LLM
    execution.

    This class intentionally does NOT:

    - access Django models
    - store summaries
    - trim conversation history
    - estimate tokens
    - know about ConversationMemory internals
    """

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        prompt: MemorySummarizerPromptV1 | None = None,
    ) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or memory_summarizer_prompt_v1

    def summarize(
        self,
        *,
        conversation: str,
    ) -> str:
        """
        Generate a compact conversation summary.

        Parameters
        ----------
        conversation:
            Plain-text conversation transcript.

        Returns
        -------
        str
            LLM-generated summary.
        """

        user_prompt = self._prompt.render_user_prompt(
            conversation=conversation,
        )

        summary = self._client.call(
            system_prompt=self._prompt.system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )

        return summary.strip()


memory_summarizer = MemorySummarizer()