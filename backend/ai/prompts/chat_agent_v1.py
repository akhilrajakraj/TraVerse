"""Version 1 conversational chat prompt."""

from __future__ import annotations

from ai.prompts.base import PromptTemplate
from ai.prompts.sanitization import (
    PROMPT_INJECTION_DEFENSE_INSTRUCTION,
    delimit_user_content,
)


class ChatAgentPromptV1(PromptTemplate):
    """Version 1 conversational prompt with user-content boundaries."""

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
                + PROMPT_INJECTION_DEFENSE_INSTRUCTION
            ),
        )

    def render_user_prompt(
        self,
        *,
        conversation_context: str,
        user_message: str,
        retrieved_destinations,
    ) -> str:
        context = (
            conversation_context.strip()
            if conversation_context.strip()
            else "No previous conversation."
        )

        destination_context = ""
        if retrieved_destinations:
            destination_context = "\n\nRetrieved Destinations:\n"
            for destination in retrieved_destinations:
                destination_context += (
                    f"- {destination.name}, {destination.city}, {destination.country}\n"
                    f"Summary: {destination.summary}\n"
                    f"Description: {destination.description}\n"
                    f"Tags: {', '.join(destination.tags)}\n\n"
                )

        return (
            "Conversation History:\n"
            f"{context}"
            f"{destination_context}\n\n"
            "Latest User Message:\n"
            f"{delimit_user_content(user_message)}\n\n"
            "Respond naturally while considering the conversation history."
        )


chat_agent_prompt_v1 = ChatAgentPromptV1()
