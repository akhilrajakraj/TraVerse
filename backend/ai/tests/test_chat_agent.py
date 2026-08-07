"""
Unit tests for the conversational Chat Agent.
"""

from __future__ import annotations

from unittest.mock import Mock

from ai.agents.chat_agent import ChatAgent
from ai.prompts.chat_agent_v1 import (
    ChatAgentPromptV1,
)


class TestChatAgentInitialization:
    """
    Verify ChatAgent initialization.
    """

    def test_uses_injected_client(self) -> None:
        """
        The injected Groq client should be used.
        """

        client = Mock()

        agent = ChatAgent(
            client=client,
        )

        assert agent._client is client

    def test_uses_injected_prompt(self) -> None:
        """
        The injected prompt should be used.
        """

        prompt = Mock(
            spec=ChatAgentPromptV1,
        )

        agent = ChatAgent(
            prompt=prompt,
        )

        assert agent._prompt is prompt


class TestChatAgent:
    """
    Verify conversational behaviour.
    """

    def setup_method(self) -> None:
        self.client = Mock()

        self.prompt = Mock(
            spec=ChatAgentPromptV1,
        )

        self.prompt.system_prompt = (
            "System Prompt"
        )

        self.prompt.render_user_prompt.return_value = (
            "Rendered User Prompt"
        )

        self.client.call.return_value = (
            "  Hello Traveller!  "
        )

        self.agent = ChatAgent(
            client=self.client,
            prompt=self.prompt,
        )

    def test_calls_render_user_prompt(self) -> None:
        """
        The prompt should render the user prompt.
        """

        self.agent.reply(
            conversation_context="Conversation",
            user_message="Hello",
        )

        self.prompt.render_user_prompt.assert_called_once_with(
            conversation_context="Conversation",
            user_message="Hello",
        )

    def test_calls_groq_client_once(self) -> None:
        """
        The Groq client should be called exactly once.
        """

        self.agent.reply(
            conversation_context="Conversation",
            user_message="Hello",
        )

        self.client.call.assert_called_once()

    def test_passes_system_prompt(self) -> None:
        """
        The configured system prompt should be forwarded.
        """

        self.agent.reply(
            conversation_context="Conversation",
            user_message="Hello",
        )

        kwargs = self.client.call.call_args.kwargs

        assert kwargs["system_prompt"] == (
            "System Prompt"
        )

    def test_passes_rendered_user_prompt(self) -> None:
        """
        The rendered prompt should be forwarded unchanged.
        """

        self.agent.reply(
            conversation_context="Conversation",
            user_message="Hello",
        )

        kwargs = self.client.call.call_args.kwargs

        assert kwargs["user_prompt"] == (
            "Rendered User Prompt"
        )

    def test_passes_temperature(self) -> None:
        """
        The chat agent should use the configured temperature.
        """

        self.agent.reply(
            conversation_context="Conversation",
            user_message="Hello",
        )

        kwargs = self.client.call.call_args.kwargs

        assert kwargs["temperature"] == 0.3

    def test_returns_trimmed_response(self) -> None:
        """
        Leading and trailing whitespace should be removed.
        """

        response = self.agent.reply(
            conversation_context="Conversation",
            user_message="Hello",
        )

        assert response == "Hello Traveller!"