"""
Packing List AI Agent.

This module contains the production Packing Agent used by TraVerse.

Responsibilities
----------------

- Build prompts
- Call the LLM provider
- Validate structured output
- Return an updated graph state

This module intentionally does NOT:

- Know about Django models
- Save to the database
- Call REST APIs
- Execute Celery tasks
- Depend on LangGraph
"""

from __future__ import annotations

from ai.agents.schemas import (
    PackingListSchema,
)
from ai.clients.groq_client import GroqClient
from ai.graphs.state import PlanningGraphState
from ai.parsers.structured_output import (
    parse_structured_output,
)
from ai.prompts.packing_agent_v1 import (
    PackingAgentPromptV1,
    packing_agent_prompt_v1,
)


class PackingAgent:
    """
    Enterprise AI Packing List Agent.

    Coordinates prompt generation,
    LLM execution,
    and structured response validation.
    """

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        prompt: PackingAgentPromptV1 | None = None,
    ) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or packing_agent_prompt_v1

    def _repair_callback(
        self,
        repair_prompt: str,
    ) -> str:
        """
        Ask the LLM to repair an invalid JSON response.
        """

        return self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            temperature=0.0,
        )

    def generate_packing_list(
        self,
        state: PlanningGraphState,
    ) -> PlanningGraphState:
        """
        Execute the Packing Agent.

        Returns a new immutable graph state.
        """

        user_prompt = self._prompt.render_user_prompt(
            trip_title=state["trip_title"],
            destination_names=state["destination_names"],
            start_date=state["start_date"],
            end_date=state["end_date"],
            traveler_count=state["traveler_count"],
            trip_notes=state["trip_notes"],
            itinerary=state["itinerary"],
            weather_forecast=state["weather_forecast"],
        )

        raw_response = self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        packing_list = parse_structured_output(
            raw_text=raw_response,
            schema=PackingListSchema,
            repair_callback=self._repair_callback,
        )

        return {
            **state,
            "packing_list": packing_list,
        }


packing_agent = PackingAgent()