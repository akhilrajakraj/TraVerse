"""
Memory Summarizer Prompt Version 1.

This prompt instructs the LLM to summarize long conversation histories
while preserving important long-term context.

The output is intentionally plain text rather than JSON because the
summary becomes an internal memory representation consumed by later
conversation turns.
"""

from __future__ import annotations

from ai.prompts.base import PromptTemplate


class MemorySummarizerPromptV1(PromptTemplate):
    """
    Prompt builder for conversation memory summarization.
    """

    def __init__(self) -> None:
        super().__init__(
            name="memory_summarizer",
            version=1,
            system_prompt="""
You are TraVerse AI's Conversation Memory Engine.

Your responsibility is to summarize long conversations into concise,
accurate long-term memory.

Never invent information.

Only summarize facts that appear in the conversation.

Preserve:

- user preferences
- travel preferences
- destinations
- accommodation choices
- transportation choices
- budget decisions
- itinerary updates
- bookings
- travel companions
- dietary requirements
- accessibility needs
- important constraints
- unresolved questions
- future plans

Remove:

- greetings
- acknowledgements
- repeated confirmations
- conversational filler
- duplicate information

The summary should:

- remain factual
- remain chronological whenever practical
- preserve important context
- reduce token usage

Return ONLY the final summary.

Do not produce JSON.

Do not use Markdown.

Do not explain your reasoning.
""".strip(),
        )

    def render_user_prompt(
        self,
        *,
        conversation: str,
    ) -> str:
        """
        Render the summarization request.
        """

        conversation = conversation.strip()

        if not conversation:
            conversation = "No conversation history."

        return f"""
Conversation History

{conversation}

Summarize the conversation into a compact memory that preserves every
important long-term detail.

Return ONLY the summary.
""".strip()


memory_summarizer_prompt_v1 = MemorySummarizerPromptV1()