"""
Version 1 conversational chat prompt.

This module defines the first production prompt used by the
TraVerse AI Chat Agent.

The prompt layer is responsible only for prompt construction.
It remains completely independent of Django models and any
specific LLM provider.
"""

from __future__ import annotations

from ai.prompts.base import PromptTemplate


class ChatAgentPromptV1(PromptTemplate):
    """
    Version 1 conversational prompt.
    """

    def __init__(self) -> None:
        super().__init__(
            name="chat_agent",
            version=1,
            system_prompt=(
                "You are TraVerse AI, an expert travel assistant.\n\n"
                "You help users understand, modify and improve their trips.\n\n"
                "Rules:\n"
                "- Respond conversationally.\n"
                "- Use previous conversation context when available.\n"
                "- Answer only travel-related questions.\n"
                "- Never invent information.\n"
                "- If information is unavailable, say so clearly.\n"
                "- Never expose internal JSON or implementation details.\n"
                "- Return plain text only.\n"
                "- Do not use Markdown code fences."
            ),
        )

    def render_user_prompt(
        self,
        *,
        conversation_context: str,
        user_message: str,
    ) -> str:
        """
        Render the user prompt.
        """

        context = (
            conversation_context.strip()
            if conversation_context.strip()
            else "No previous conversation."
        )

        return (
            "Conversation History:\n"
            f"{context}\n\n"
            "Latest User Message:\n"
            f"{user_message}\n\n"
            "Respond naturally while considering the conversation history."
        )


chat_agent_prompt_v1 = ChatAgentPromptV1()