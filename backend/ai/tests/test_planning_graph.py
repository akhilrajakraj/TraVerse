"""
Unit tests for the LangGraph planning workflow.

These tests verify that the planning graph delegates execution to the
Travel Planner agent and returns the updated graph state.

No Django.
No database.
No Celery.
No external LLM calls.
"""

from __future__ import annotations

from unittest.mock import patch

from langgraph.graph.state import CompiledStateGraph

from ai.agents.schemas import (
    BudgetEstimateSchema,
    BudgetLineItemEstimateSchema,
    ItineraryPlanSchema,
    DailyWeatherSchema,
    WeatherForecastSchema,
)
from ai.graphs.planning_graph import (
    build_planning_graph,
    run_planning_graph,
)
from ai.graphs.state import PlanningGraphState


def test_build_planning_graph_returns_compiled_graph():
    """
    The planning graph should compile successfully.
    """

    graph = build_planning_graph()

    assert isinstance(
        graph,
        CompiledStateGraph,
    )

@patch("ai.graphs.planning_graph.weather_agent")
@patch("ai.graphs.planning_graph.budget_agent")
@patch("ai.graphs.planning_graph.travel_planner_agent")
def test_run_planning_graph(
    mock_travel_agent,
    mock_budget_agent,
    mock_weather_agent,
):
    """
    The planning graph should delegate execution to the Travel Planner
    agent and return the updated PlanningGraphState.
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
    }

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
    
    budget = BudgetEstimateSchema(
        line_items=[
            BudgetLineItemEstimateSchema(
                category="food",
                description="Meals",
                estimated_amount=150.0,
            )
        ]
    )
    
    weather = WeatherForecastSchema(
        days=[
            DailyWeatherSchema(
                date="2026-09-10",
                condition="Sunny",
                high_f=84,
                low_f=72,
                precipitation_chance=10,
            )
        ]
    )

    travel_state: PlanningGraphState = {
        **state,
        "itinerary": itinerary,
    }
    
    mock_travel_agent.plan.return_value = travel_state
    
    budget_state = {
        **travel_state,
        "budget_estimate": budget,
    }
    
    mock_budget_agent.estimate_budget.return_value = budget_state
    
    weather_state = {
        **budget_state,
        "weather_forecast": weather,
    }

    
    mock_weather_agent.estimate_weather.return_value = weather_state

    result = run_planning_graph(
        state,
    )

    #
    # LangGraph preserves only keys declared in PlanningGraphState.
    #

    assert result["trip_title"] == state["trip_title"]

    assert result["destination_names"] == state["destination_names"]

    assert result["start_date"] == state["start_date"]

    assert result["end_date"] == state["end_date"]

    assert result["traveler_count"] == state["traveler_count"]

    assert result["trip_notes"] == state["trip_notes"]

    assert result["itinerary"] == itinerary
    
    assert result["budget_estimate"] == budget
    
    assert result["weather_forecast"] == weather

    mock_travel_agent.plan.assert_called_once_with(
        state,
    )
    
    mock_budget_agent.estimate_budget.assert_called_once_with(
        travel_state,   
    )

    mock_weather_agent.estimate_weather.assert_called_once_with(
        budget_state,
    )