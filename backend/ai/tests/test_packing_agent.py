"""
Unit tests for the Packing List AI agent.

These tests exercise only the plain-Python AI layer.

No Django.
No database.
No Celery.
No LangGraph.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from ai.agents.packing_agent import PackingAgent
from ai.agents.schemas import (
    PackingItemSchema,
    PackingListSchema,
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
    DailyWeatherSchema,
    WeatherForecastSchema,
)
from ai.graphs.state import PlanningGraphState


def _build_itinerary() -> ItineraryPlanSchema:
    """
    Construct a representative itinerary.
    """

    return ItineraryPlanSchema(
        days=[
            ItineraryDaySchema(
                day_number=1,
                date="2026-09-10",
                summary="Arrival",
                items=[
                    ItineraryItemSchema(
                        title="Hotel Check-in",
                        description="Check into hotel.",
                        location="Kyoto",
                        start_time="15:00",
                        end_time="16:00",
                        estimated_cost_usd=120.0,
                    )
                ],
            )
        ]
    )


def _build_weather() -> WeatherForecastSchema:
    """
    Representative weather forecast.
    """

    return WeatherForecastSchema(
        days=[
            DailyWeatherSchema(
                date="2026-09-10",
                condition="Sunny",
                high_f=84,
                low_f=70,
                precipitation_chance=10,
            )
        ]
    )


def test_generate_packing_list_returns_updated_state():
    """
    PackingAgent should return updated graph state.
    """

    fake_client = MagicMock()

    fake_client.call.return_value = """
    {
      "items": [
        {
          "category": "clothing",
          "item": "Rain Jacket",
          "quantity": 1,
          "reason": "Possible weather changes."
        }
      ]
    }
    """

    state: PlanningGraphState = {
        "trip_title": "Japan Tour",
        "destination_names": ["Kyoto"],
        "start_date": "2026-09-10",
        "end_date": "2026-09-15",
        "traveler_count": 2,
        "trip_notes": "Interested in temples.",
        "itinerary": _build_itinerary(),
        "weather_forecast": _build_weather(),
    }

    agent = PackingAgent(
        client=fake_client,
    )

    updated_state = agent.generate_packing_list(
        state,
    )

    assert updated_state is not state

    assert updated_state["trip_title"] == state["trip_title"]

    assert "packing_list" in updated_state

    assert isinstance(
        updated_state["packing_list"],
        PackingListSchema,
    )

    assert (
        updated_state["packing_list"]
        .items[0]
        .category
        == "clothing"
    )

    fake_client.call.assert_called_once()


@patch("ai.agents.packing_agent.parse_structured_output")
def test_generate_packing_list_calls_structured_output_parser(
    mock_parser,
):
    """
    PackingAgent should delegate validation to parser.
    """

    packing = PackingListSchema(
        items=[
            PackingItemSchema(
                category="clothing",
                item="Rain Jacket",
                quantity=1,
                reason="Possible rain.",
            )
        ]
    )

    mock_parser.return_value = packing

    fake_client = MagicMock()

    fake_client.call.return_value = "raw llm response"

    state: PlanningGraphState = {
        "trip_title": "Japan Tour",
        "destination_names": ["Kyoto"],
        "start_date": "2026-09-10",
        "end_date": "2026-09-15",
        "traveler_count": 2,
        "trip_notes": "Interested in temples.",
        "itinerary": _build_itinerary(),
        "weather_forecast": _build_weather(),
    }

    agent = PackingAgent(
        client=fake_client,
    )

    result = agent.generate_packing_list(
        state,
    )

    assert result["packing_list"] is packing

    mock_parser.assert_called_once()

    fake_client.call.assert_called_once()