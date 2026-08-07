"""
Unit tests for the Conversation Memory Summarizer.
"""

from __future__ import annotations

from unittest.mock import Mock

from ai.memory.memory_summarizer import MemorySummarizer
from ai.prompts.memory_summarizer_v1 import (
    MemorySummarizerPromptV1,
)


class TestMemorySummarizerInitialization:
    """
    Verify MemorySummarizer initialization.
    """

    def test_uses_injected_client(self) -> None:
        """
        The injected Groq client should be used.
        """

        client = Mock()

        summarizer = MemorySummarizer(
            client=client,
        )

        assert summarizer._client is client

    def test_uses_injected_prompt(self) -> None:
        """
        The injected prompt should be used.
        """

        prompt = Mock(spec=MemorySummarizerPromptV1)

        summarizer = MemorySummarizer(
            prompt=prompt,
        )

        assert summarizer._prompt is prompt


class TestMemorySummarizer:
    """
    Verify summarization behaviour.
    """

    def setup_method(self) -> None:
        self.client = Mock()

        self.prompt = Mock(spec=MemorySummarizerPromptV1)

        self.prompt.system_prompt = "System Prompt"

        self.prompt.render_user_prompt.return_value = (
            "Rendered User Prompt"
        )

        self.client.call.return_value = (
            "  Compact Conversation Summary  "
        )

        self.summarizer = MemorySummarizer(
            client=self.client,
            prompt=self.prompt,
        )

    def test_calls_render_user_prompt(self) -> None:
        """
        The prompt builder should render the user prompt.
        """

        self.summarizer.summarize(
            conversation="Conversation History",
        )

        self.prompt.render_user_prompt.assert_called_once_with(
            conversation="Conversation History",
        )

    def test_calls_groq_client_once(self) -> None:
        """
        The Groq client should be called exactly once.
        """

        self.summarizer.summarize(
            conversation="Conversation History",
        )

        self.client.call.assert_called_once()

    def test_passes_system_prompt(self) -> None:
        """
        The configured system prompt should be forwarded.
        """

        self.summarizer.summarize(
            conversation="Conversation History",
        )

        kwargs = self.client.call.call_args.kwargs

        assert kwargs["system_prompt"] == "System Prompt"

    def test_passes_rendered_user_prompt(self) -> None:
        """
        The rendered prompt should be forwarded unchanged.
        """

        self.summarizer.summarize(
            conversation="Conversation History",
        )

        kwargs = self.client.call.call_args.kwargs

        assert kwargs["user_prompt"] == (
            "Rendered User Prompt"
        )

    def test_passes_temperature(self) -> None:
        """
        The summarizer should use the configured temperature.
        """

        self.summarizer.summarize(
            conversation="Conversation History",
        )

        kwargs = self.client.call.call_args.kwargs

        assert kwargs["temperature"] == 0.2

    def test_returns_trimmed_summary(self) -> None:
        """
        Leading and trailing whitespace should be removed.
        """

        summary = self.summarizer.summarize(
            conversation="Conversation History",
        )

        assert summary == "Compact Conversation Summary"
        
    def test_empty_summary_is_returned(self) -> None:
        """
        Empty summaries should be returned unchanged.
        """

        self.client.call.return_value = ""

        summary = self.summarizer.summarize(
        conversation="Conversation History",
        )

        assert summary == ""