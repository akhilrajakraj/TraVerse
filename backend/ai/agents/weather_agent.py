"""
Weather Forecast AI Agent.

This module contains the production Weather Agent used by TraVerse.

Responsibilities
----------------
- Build prompts
- Call the LLM provider
- Execute weather tools
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

import json

from datetime import date

from ai.agents.schemas import WeatherForecastSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import PlanningGraphState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.weather_agent_v1 import (
    WeatherAgentPromptV1,
    weather_agent_prompt_v1,
)
from ai.tools.weather_tool import get_typical_weather


class WeatherAgent:
    """
    Enterprise AI Weather Forecast Agent.

    Coordinates prompt generation,
    LLM execution with tool calling,
    and structured response validation.
    """

    def __init__(
        self,
        *,
        client: GroqClient | None = None,
        prompt: WeatherAgentPromptV1 | None = None,
    ) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or weather_agent_prompt_v1

    def _tool_executor(
        self,
        tool_name: str,
        arguments: dict,
    ) -> str:
        """
        Execute supported AI tools.
        """

        if tool_name == "get_typical_weather":
            result = get_typical_weather(
                destination=arguments["destination"],
                travel_date=date.fromisoformat(
                    arguments["travel_date"]
                ),
            )

            return json.dumps(result)

        raise ValueError(
            f"Unsupported tool '{tool_name}'."
        )

    def _repair_callback(
        self,
        repair_prompt: str,
    ) -> str:
        """
        Ask the LLM to repair invalid JSON.

        Repair does not require tool calling.
        """

        return self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            temperature=0.0,
        )

    def estimate_weather(
        self,
        state: PlanningGraphState,
    ) -> PlanningGraphState:
        """
        Execute the Weather Agent.

        Returns a new immutable graph state.
        """

        user_prompt = self._prompt.render_user_prompt(
            trip_title=state["trip_title"],
            destination_names=state["destination_names"],
            itinerary=state["itinerary"],
        )

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_typical_weather",
                    "description": (
                        "Retrieve a deterministic weather estimate "
                        "for a destination and travel date."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "string",
                            },
                            "travel_date": {
                                "type": "string",
                                "format": "date",
                            },
                        },
                        "required": [
                            "destination",
                            "travel_date",
                        ],
                    },
                },
            }
        ]

        raw_response = self._client.call_with_tools(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            tools=tools,
            tool_executor=self._tool_executor,
            temperature=0.3,
        )

        weather_forecast = parse_structured_output(
            raw_text=raw_response,
            schema=WeatherForecastSchema,
            repair_callback=self._repair_callback,
        )

        return {
            **state,
            "weather_forecast": weather_forecast,
        }


weather_agent = WeatherAgent()