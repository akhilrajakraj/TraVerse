from __future__ import annotations

import json
from datetime import date

from ai.agents.schemas import WeatherForecastSchema
from ai.clients.groq_client import GroqClient
from ai.graphs.state import PlanningGraphState
from ai.parsers.structured_output import parse_structured_output
from ai.prompts.weather_agent_v1 import WeatherAgentPromptV1, weather_agent_prompt_v1
from ai.tools.weather_tool import get_typical_weather


class WeatherAgent:
    def __init__(self, *, client: GroqClient | None = None, prompt: WeatherAgentPromptV1 | None = None) -> None:
        self._client = client or GroqClient()
        self._prompt = prompt or weather_agent_prompt_v1

    def _tool_executor(self, tool_name: str, arguments: dict) -> str:
        if tool_name == "get_typical_weather":
            result = get_typical_weather(
                destination=arguments["destination"],
                travel_date=date.fromisoformat(arguments["travel_date"]),
            )
            return json.dumps(result)
        raise ValueError(f"Unsupported tool '{tool_name}'.")

    def _repair_callback(self, repair_prompt: str) -> str:
        return self._client.call(
            system_prompt=self._prompt.SYSTEM_PROMPT,
            user_prompt=repair_prompt,
            temperature=0.0,
            json_mode=True,
        )

    def estimate_weather(self, state: PlanningGraphState) -> PlanningGraphState:
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
                    "description": "Retrieve a deterministic weather estimate for a destination and travel date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {"type": "string"},
                            "travel_date": {"type": "string", "format": "date"},
                        },
                        "required": ["destination", "travel_date"],
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
            json_mode=True,
        )

        weather_forecast = parse_structured_output(
            raw_text=raw_response,
            schema=WeatherForecastSchema,
            repair_callback=self._repair_callback,
        )

        return {**state, "weather_forecast": weather_forecast}


weather_agent = WeatherAgent()
