"""
Travel Planner AI Agent.

This module contains the first production AI agent used by TraVerse.

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

from ai.agents.schemas import ItineraryPlanSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import PlanningGraphState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.planner_v1 import (
    TravelPlannerPromptV1,
    travel_planner_prompt_v1,
)


class TravelPlannerAgent:
    """
    Enterprise AI Travel Planner.

    Coordinates prompt generation,
    LLM execution,
    and structured response validation.
    """

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        prompt: TravelPlannerPromptV1 | None = None,
    ) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or travel_planner_prompt_v1

    def _repair_callback(
        self,
        repair_prompt: str,
    ) -> str:
        """
        Ask the LLM to repair an invalid JSON response.
        """

        return self._client.call(
            system_prompt=self._prompt.system_prompt,
            user_prompt=repair_prompt,
            temperature=0.0,
        )

    def plan(
        self,
        state: PlanningGraphState,
    ) -> PlanningGraphState:
        """
        Execute the Travel Planner agent.

        Returns a new immutable graph state.
        """

        user_prompt = self._prompt.render_user_prompt(
            trip_title=state["trip_title"],
            destination_names=state["destination_names"],
            start_date=state["start_date"],
            end_date=state["end_date"],
            traveler_count=state["traveler_count"],
            trip_notes=state["trip_notes"],
        )

        raw_response = self._client.call(
            system_prompt=self._prompt.system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )

        itinerary = parse_structured_output(
            raw_text=raw_response,
            schema=ItineraryPlanSchema,
            repair_callback=self._repair_callback,
        )

        return {
            **state,
            "itinerary": itinerary,
        }


travel_planner_agent = TravelPlannerAgent()