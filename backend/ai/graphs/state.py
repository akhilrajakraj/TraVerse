"""
Shared state definitions for AI graph execution.

The planning graph passes a single state object between graph nodes.
Each node reads the current state, performs its work, and returns an
updated immutable state.

The graph state intentionally contains only primitive values and
validated Pydantic models. It is completely independent of Django
models.
"""

from __future__ import annotations

from typing import TypedDict

from typing_extensions import NotRequired

from ai.agents.schemas import (
    ItineraryPlanSchema,
    BudgetEstimateSchema,
    WeatherForecastSchema,
)


class PlanningGraphState(TypedDict):
    """
    Shared execution state for the AI planning workflow.

    This TypedDict is the canonical contract shared by:

    - Django service layer
    - AI agents
    - Prompt builders
    - LangGraph workflow
    """

    # ------------------------------------------------------------------
    # Trip Context
    # ------------------------------------------------------------------

    trip_title: str

    destination_names: list[str]

    start_date: str

    end_date: str

    # ------------------------------------------------------------------
    # Traveler Information
    # ------------------------------------------------------------------

    traveler_count: int

    trip_notes: str

    # ------------------------------------------------------------------
    # AI Outputs
    # ------------------------------------------------------------------

    itinerary: NotRequired[ItineraryPlanSchema]
    
    budget_estimate: NotRequired[BudgetEstimateSchema]

    weather_forecast: NotRequired[WeatherForecastSchema]

    # ------------------------------------------------------------------
    # Execution Metadata
    # ------------------------------------------------------------------

    error: NotRequired[str]