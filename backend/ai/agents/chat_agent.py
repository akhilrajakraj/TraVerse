"""
Conversational AI agent for TraVerse.
"""

from __future__ import annotations

from ai.clients.groq_client import GroqClient
from ai.prompts.chat_agent_v1 import (
    ChatAgentPromptV1,
    chat_agent_prompt_v1,
)


class ChatAgent:
    """
    Handles conversational interactions with the user.
    """

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        prompt: ChatAgentPromptV1 | None = None,
    ) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or chat_agent_prompt_v1

    def reply(
        self,
        *,
        conversation_context: str,
        user_message: str,
    ) -> str:
        """
        Generate a conversational response.
        """

        user_prompt = self._prompt.render_user_prompt(
            conversation_context=conversation_context,
            user_message=user_message,
        )

        response = self._client.call(
            system_prompt=self._prompt.system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        return response.strip()