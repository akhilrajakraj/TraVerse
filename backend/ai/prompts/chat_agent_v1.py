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
                "- Use the authoritative trip data when answering questions about the current trip.\n"
                "- Use previous conversation context when available.\n"
                "- Use only information present in trip data, conversation history, or retrieved destinations.\n"
                "- Never invent trip details, costs, dates, activities, or reservations.\n"
                "- If the requested information is not present, say exactly what is unavailable.\n"
                "- When asked about cost, use the provided budget and itinerary cost data before asking the user to repeat details.\n"
                "- Answer only travel-related questions.\n"
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
        trip_context: str = "",
        retrieved_destinations=None,
    ) -> str:
        context = (
            conversation_context.strip()
            if conversation_context.strip()
            else "No previous conversation."
        )

        authoritative_trip_context = (
            trip_context.strip()
            if trip_context.strip()
            else "No trip data is available."
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
            "Authoritative Trip Data:\n"
            f"{authoritative_trip_context}\n\n"
            "Conversation History:\n"
            f"{context}"
            f"{destination_context}\n\n"
            "Latest User Message:\n"
            f"{delimit_user_content(user_message)}\n\n"
            "Respond naturally using the authoritative trip data first, then conversation history and retrieved destinations as supporting context."
        )


chat_agent_prompt_v1 = ChatAgentPromptV1()
