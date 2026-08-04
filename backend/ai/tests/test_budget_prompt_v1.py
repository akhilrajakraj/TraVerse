"""
Tests for the Budget Agent prompt builder.
"""

from __future__ import annotations

from ai.agents.schemas import (
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
)
from ai.prompts.budget_agent_v1 import (
    budget_agent_prompt_v1,
)


def _build_itinerary() -> ItineraryPlanSchema:
    """
    Build a representative itinerary for prompt rendering tests.
    """

    return ItineraryPlanSchema(
        days=[
            ItineraryDaySchema(
                day_number=1,
                date="2026-08-10",
                summary="Arrival in Tokyo",
                items=[
                    ItineraryItemSchema(
                        title="Hotel Check-in",
                        description="Check into hotel.",
                        location="Shinjuku",
                        start_time="15:00",
                        end_time="16:00",
                        estimated_cost_usd=120.0,
                    ),
                    ItineraryItemSchema(
                        title="Dinner",
                        description="Local sushi restaurant.",
                        location="Shinjuku",
                        start_time="19:00",
                        end_time="20:30",
                        estimated_cost_usd=40.0,
                    ),
                ],
            ),
        ],
    )


def test_system_prompt_exists() -> None:
    """
    System prompt should not be empty.
    """

    assert budget_agent_prompt_v1.SYSTEM_PROMPT
    assert "JSON" in budget_agent_prompt_v1.SYSTEM_PROMPT
    assert "budget" in budget_agent_prompt_v1.SYSTEM_PROMPT.lower()


def test_render_user_prompt_contains_trip_information() -> None:
    """
    Rendered prompt should contain all supplied trip metadata.
    """

    prompt = budget_agent_prompt_v1.render_user_prompt(
        trip_title="Japan Adventure",
        destination_names=["Tokyo"],
        start_date="2026-08-10",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="Vegetarian meals preferred.",
        itinerary=_build_itinerary(),
    )

    assert "Japan Adventure" in prompt
    assert "Tokyo" in prompt
    assert "2026-08-10" in prompt
    assert "2026-08-15" in prompt
    assert "Vegetarian meals preferred." in prompt


def test_render_user_prompt_contains_itinerary() -> None:
    """
    Prompt should include itinerary summaries and activities.
    """

    prompt = budget_agent_prompt_v1.render_user_prompt(
        trip_title="Japan Adventure",
        destination_names=["Tokyo"],
        start_date="2026-08-10",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="",
        itinerary=_build_itinerary(),
    )

    assert "Day 1" in prompt
    assert "Arrival in Tokyo" in prompt
    assert "Hotel Check-in" in prompt
    assert "Dinner" in prompt


def test_empty_notes_are_replaced() -> None:
    """
    Empty notes should render the default placeholder.
    """

    prompt = budget_agent_prompt_v1.render_user_prompt(
        trip_title="Japan Adventure",
        destination_names=["Tokyo"],
        start_date="2026-08-10",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="",
        itinerary=_build_itinerary(),
    )

    assert "No additional notes." in prompt