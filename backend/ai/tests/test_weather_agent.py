"""
Tests for the Weather Agent.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ai.agents.schemas import (
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
    WeatherForecastSchema,
)
from ai.agents.weather_agent import WeatherAgent
from ai.graphs.state import PlanningGraphState


def build_state() -> PlanningGraphState:
    itinerary = ItineraryPlanSchema(
        days=[
            ItineraryDaySchema(
                day_number=1,
                date="2026-07-10",
                summary="Tokyo exploration",
                items=[
                    ItineraryItemSchema(
                        start_time="09:00",
                        end_time="12:00",
                        title="Temple",
                        description="Visit Senso-ji",
                    )
                ],
            )
        ]
    )

    return {
        "trip_title": "Japan Trip",
        "destination_names": ["Tokyo"],
        "start_date": "2026-07-10",
        "end_date": "2026-07-10",
        "traveler_count": 2,
        "trip_notes": "",
        "itinerary": itinerary,
    }


class TestWeatherAgent:

    def test_estimate_weather(self):
        client = MagicMock()

        client.call_with_tools.return_value = """
        {
          "days":[
            {
              "date":"2026-07-10",
              "condition":"Warm",
              "high_f":86,
              "low_f":70,
              "precipitation_chance":35
            }
          ]
        }
        """

        agent = WeatherAgent(
            client=client,
        )

        result = agent.estimate_weather(
            build_state(),
        )

        assert "weather_forecast" in result
        assert isinstance(
            result["weather_forecast"],
            WeatherForecastSchema,
        )

        client.call_with_tools.assert_called_once()

    def test_tool_executor(self):
        agent = WeatherAgent(
            client=MagicMock(),
        )

        result = agent._tool_executor(
            "get_typical_weather",
            {
                "destination": "Tokyo",
                "travel_date": "2026-07-10",
            },
        )

        assert '"destination": "Tokyo"' in result
        assert '"season": "summer"' in result

    def test_unknown_tool(self):
        agent = WeatherAgent(
            client=MagicMock(),
        )

        try:
            agent._tool_executor(
                "unknown_tool",
                {},
            )
        except ValueError as exc:
            assert "Unsupported tool" in str(exc)
        else:
            assert False