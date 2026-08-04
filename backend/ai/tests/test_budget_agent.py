"""
Unit tests for the Budget Estimation AI agent.

These tests exercise only the plain-Python AI layer.

No Django.
No database.
No Celery.
No LangGraph.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from ai.agents.budget_agent import BudgetAgent
from ai.agents.schemas import (
    BudgetEstimateSchema,
    BudgetLineItemEstimateSchema,
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
)
from ai.graphs.state import PlanningGraphState


def _build_itinerary() -> ItineraryPlanSchema:
    """
    Construct a representative itinerary for testing.
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
                    ),
                ],
            ),
        ],
    )


def test_estimate_budget_returns_updated_state():
    """
    BudgetAgent should return a new PlanningGraphState
    containing a validated BudgetEstimateSchema.
    """

    fake_client = MagicMock()

    fake_client.call.return_value = """
    {
        "line_items": [
            {
                "category": "food",
                "description": "Meals",
                "estimated_amount": 150.0
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
        "trip_notes": "Interested in temples.",
        "itinerary": _build_itinerary(),
    }

    agent = BudgetAgent(
        client=fake_client,
    )

    updated_state = agent.estimate_budget(
        state,
    )

    assert updated_state is not state

    assert updated_state["trip_title"] == state["trip_title"]

    assert (
        updated_state["destination_names"]
        == state["destination_names"]
    )

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

    assert updated_state["itinerary"] is state["itinerary"]

    assert "budget_estimate" in updated_state

    assert isinstance(
        updated_state["budget_estimate"],
        BudgetEstimateSchema,
    )

    assert (
        updated_state["budget_estimate"]
        .line_items[0]
        .category
        == "food"
    )

    fake_client.call.assert_called_once()


@patch("ai.agents.budget_agent.parse_structured_output")
def test_estimate_budget_calls_structured_output_parser(
    mock_parser,
):
    """
    BudgetAgent should delegate response validation
    to the structured output parser.
    """

    budget = BudgetEstimateSchema(
        line_items=[
            BudgetLineItemEstimateSchema(
                category="food",
                description="Meals",
                estimated_amount=150.0,
            )
        ]
    )

    mock_parser.return_value = budget

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
        "trip_notes": "Interested in temples.",
        "itinerary": _build_itinerary(),
    }

    agent = BudgetAgent(
        client=fake_client,
    )

    result = agent.estimate_budget(
        state,
    )

    assert result["budget_estimate"] is budget

    mock_parser.assert_called_once()

    fake_client.call.assert_called_once()