"""
Unit tests for the Travel Planner AI agent.

These tests exercise only the plain-Python AI layer.

No Django.
No database.
No Celery.
No LangGraph.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from ai.agents.schemas import ItineraryPlanSchema
from ai.agents.travel_planner import TravelPlannerAgent
from ai.graphs.state import PlanningGraphState


def test_plan_returns_updated_state():
    """
    The TravelPlannerAgent should return a new PlanningGraphState
    containing a validated itinerary.
    """

    fake_client = MagicMock()

    fake_client.call.return_value = """
    {
        "days": [
            {
                "day_number": 1,
                "date": "2026-09-10",
                "summary": "Arrival",
                "items": [
                    {
                        "title": "Hotel Check-in",
                        "description": "",
                        "estimated_cost_usd": 120
                    }
                ]
            }
        ]
    }
    """

    state: PlanningGraphState = {
        "trip_title": "Japan Tour",
        "destination_names": [
            "Kyoto",
        ],
        "start_date": "2026-09-10",
        "end_date": "2026-09-15",
        "traveler_count": 2,
        "trip_notes": "Interested in temples and local cuisine.",
    }

    agent = TravelPlannerAgent(
        client=fake_client,
    )

    updated_state = agent.plan(
        state,
    )

    assert updated_state is not state

    assert updated_state["trip_title"] == state["trip_title"]

    assert updated_state["destination_names"] == state["destination_names"]

    assert updated_state["start_date"] == state["start_date"]

    assert updated_state["end_date"] == state["end_date"]

    assert (
        updated_state["traveler_count"]
        == state["traveler_count"]
    )

    assert (
        updated_state["trip_notes"]
        == state["trip_notes"]
    )

    assert "itinerary" in updated_state

    assert isinstance(
        updated_state["itinerary"],
        ItineraryPlanSchema,
    )

    assert (
        updated_state["itinerary"]
        .days[0]
        .day_number
        == 1
    )

    fake_client.call.assert_called_once()


@patch("ai.agents.travel_planner.parse_structured_output")
def test_plan_calls_structured_output_parser(
    mock_parser,
):
    """
    The TravelPlannerAgent should delegate response validation to the
    structured output parser.
    """

    itinerary = ItineraryPlanSchema.model_validate(
        {
            "days": [
                {
                    "day_number": 1,
                    "date": "2026-09-10",
                    "summary": "Arrival",
                    "items": [
                        {
                            "title": "Hotel Check-in",
                            "description": "",
                            "estimated_cost_usd": 120,
                        }
                    ],
                }
            ]
        }
    )

    mock_parser.return_value = itinerary

    fake_client = MagicMock()

    fake_client.call.return_value = "raw llm response"

    state: PlanningGraphState = {
        "trip_title": "Japan Tour",
        "destination_names": [
            "Kyoto",
        ],
        "start_date": "2026-09-10",
        "end_date": "2026-09-15",
        "traveler_count": 2,
        "trip_notes": "Interested in temples and local cuisine.",
    }

    agent = TravelPlannerAgent(
        client=fake_client,
    )

    result = agent.plan(
        state,
    )

    assert result["itinerary"] is itinerary

    mock_parser.assert_called_once()

    fake_client.call.assert_called_once()