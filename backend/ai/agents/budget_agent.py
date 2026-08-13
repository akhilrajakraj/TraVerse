"""
Budget Estimation AI Agent.
"""

from __future__ import annotations

from ai.agents.schemas import BudgetEstimateSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import PlanningGraphState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.budget_agent_v1 import BudgetAgentPromptV1, budget_agent_prompt_v1


class BudgetAgent:
    """Enterprise AI Budget Estimation Agent."""

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        prompt: BudgetAgentPromptV1 | None = None,
    ) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or budget_agent_prompt_v1

    def _repair_callback(self, repair_prompt: str) -> str:
        return self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            temperature=0.0,
            json_mode=True,
        )

    def estimate_budget(self, state: PlanningGraphState) -> PlanningGraphState:
        user_prompt = self._prompt.render_user_prompt(
            trip_title=state["trip_title"],
            destination_names=state["destination_names"],
            start_date=state["start_date"],
            end_date=state["end_date"],
            traveler_count=state["traveler_count"],
            trip_notes=state["trip_notes"],
            itinerary=state["itinerary"],
        )

        raw_response = self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3,
            json_mode=True,
        )

        budget_estimate = parse_structured_output(
            raw_text=raw_response,
            schema=BudgetEstimateSchema,
            repair_callback=self._repair_callback,
        )

        return {**state, "budget_estimate": budget_estimate}


budget_agent = BudgetAgent()
