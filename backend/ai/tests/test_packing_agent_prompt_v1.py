"""
Tests for the Packing Agent prompt builder.
"""

from __future__ import annotations

from ai.agents.schemas import (
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
    DailyWeatherSchema,
    WeatherForecastSchema,
)
from ai.prompts.packing_agent_v1 import (
    packing_agent_prompt_v1,
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
                        title="City Walk",
                        description="Evening walk.",
                        location="Shinjuku",
                        start_time="18:00",
                        end_time="20:00",
                        estimated_cost_usd=0.0,
                    ),
                ],
            ),
        ],
    )


def _build_weather() -> WeatherForecastSchema:
    """
    Build representative weather data.
    """

    return WeatherForecastSchema(
        days=[
            DailyWeatherSchema(
                date="2026-08-10",
                condition="Rain",
                high_f=82,
                low_f=71,
                precipitation_chance=80,
            )
        ]
    )


def test_system_prompt_exists() -> None:
    """
    System prompt should not be empty.
    """

    assert packing_agent_prompt_v1.SYSTEM_PROMPT
    assert "JSON" in packing_agent_prompt_v1.SYSTEM_PROMPT
    assert "packing" in (
        packing_agent_prompt_v1.SYSTEM_PROMPT.lower()
    )


def test_render_user_prompt_contains_trip_information() -> None:
    """
    Rendered prompt should contain supplied trip metadata.
    """

    prompt = packing_agent_prompt_v1.render_user_prompt(
        trip_title="Japan Adventure",
        destination_names=["Tokyo"],
        start_date="2026-08-10",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="Photography trip.",
        itinerary=_build_itinerary(),
        weather_forecast=_build_weather(),
    )

    assert "Japan Adventure" in prompt
    assert "Tokyo" in prompt
    assert "2026-08-10" in prompt
    assert "2026-08-15" in prompt
    assert "Photography trip." in prompt


def test_render_user_prompt_contains_itinerary_and_weather() -> None:
    """
    Prompt should contain itinerary and weather context.
    """

    prompt = packing_agent_prompt_v1.render_user_prompt(
        trip_title="Japan Adventure",
        destination_names=["Tokyo"],
        start_date="2026-08-10",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="",
        itinerary=_build_itinerary(),
        weather_forecast=_build_weather(),
    )

    assert "Day 1" in prompt
    assert "Arrival in Tokyo" in prompt
    assert "Hotel Check-in" in prompt
    assert "City Walk" in prompt
    assert "Rain" in prompt
    assert "82" in prompt


def test_empty_notes_are_replaced() -> None:
    """
    Empty notes should render the default placeholder.
    """

    prompt = packing_agent_prompt_v1.render_user_prompt(
        trip_title="Japan Adventure",
        destination_names=["Tokyo"],
        start_date="2026-08-10",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="",
        itinerary=_build_itinerary(),
        weather_forecast=_build_weather(),
    )

    assert "No additional notes." in prompt