from __future__ import annotations

from ai.agents.schemas import PackingListSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import PlanningGraphState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.packing_agent_v1 import PackingAgentPromptV1, packing_agent_prompt_v1


class PackingAgent:
    def __init__(self, *, client: GroqClient | None = None, prompt: PackingAgentPromptV1 | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or packing_agent_prompt_v1

    def _repair_callback(self, repair_prompt: str) -> str:
        return self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            temperature=0.0,
            json_mode=True,
        )

    def generate_packing_list(self, state: PlanningGraphState) -> PlanningGraphState:
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
            json_mode=True,
        )

        packing_list = parse_structured_output(
            raw_text=raw_response,
            schema=PackingListSchema,
            repair_callback=self._repair_callback,
        )

        return {**state, "packing_list": packing_list}


packing_agent = PackingAgent()
