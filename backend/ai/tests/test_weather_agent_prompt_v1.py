"""
Tests for the Weather Agent Prompt Version 1.
"""

from __future__ import annotations

from ai.agents.schemas import (
    ItineraryDaySchema,
    ItineraryItemSchema,
    ItineraryPlanSchema,
)
from ai.prompts.weather_agent_v1 import (
    WeatherAgentPromptV1,
)


def build_sample_itinerary() -> ItineraryPlanSchema:
    """
    Build a deterministic itinerary for prompt testing.
    """

    return ItineraryPlanSchema(
        days=[
            ItineraryDaySchema(
                day_number=1,
                date="2026-07-10",
                summary="Explore central Tokyo.",
                items=[
                    ItineraryItemSchema(
                        start_time="09:00",
                        end_time="12:00",
                        title="Senso-ji Temple",
                        description="Visit the historic temple.",
                    ),
                    ItineraryItemSchema(
                        start_time="14:00",
                        end_time="17:00",
                        title="Akihabara",
                        description="Explore electronics and anime district.",
                    ),
                ],
            ),
            ItineraryDaySchema(
                day_number=2,
                date="2026-07-11",
                summary="Nature and relaxation.",
                items=[
                    ItineraryItemSchema(
                        start_time="10:00",
                        end_time="15:00",
                        title="Ueno Park",
                        description="Walk through gardens and museums.",
                    ),
                ],
            ),
        ]
    )


class TestWeatherAgentPromptMetadata:
    """
    Validate prompt metadata.
    """

    def test_version(self):
        assert WeatherAgentPromptV1.VERSION == "v1"

    def test_name(self):
        assert WeatherAgentPromptV1.NAME == "weather-agent-v1"


class TestWeatherSystemPrompt:
    """
    Validate the system prompt.
    """

    def test_mentions_weather(self):
        assert "weather" in WeatherAgentPromptV1.SYSTEM_PROMPT.lower()

    def test_requires_json(self):
        assert "json" in WeatherAgentPromptV1.SYSTEM_PROMPT.lower()

    def test_mentions_tool(self):
        assert "tool" in WeatherAgentPromptV1.SYSTEM_PROMPT.lower()


class TestWeatherUserPrompt:
    """
    Validate rendered user prompts.
    """

    def setup_method(self):
        self.prompt = WeatherAgentPromptV1()

        self.itinerary = build_sample_itinerary()

    def test_contains_trip_title(self):
        rendered = self.prompt.render_user_prompt(
            trip_title="Japan Adventure",
            destination_names=["Tokyo"],
            itinerary=self.itinerary,
        )

        assert "Japan Adventure" in rendered

    def test_contains_destination(self):
        rendered = self.prompt.render_user_prompt(
            trip_title="Japan Adventure",
            destination_names=["Tokyo"],
            itinerary=self.itinerary,
        )

        assert "Tokyo" in rendered

    def test_contains_itinerary_summary(self):
        rendered = self.prompt.render_user_prompt(
            trip_title="Japan Adventure",
            destination_names=["Tokyo"],
            itinerary=self.itinerary,
        )

        assert "Explore central Tokyo." in rendered

    def test_contains_activity_titles(self):
        rendered = self.prompt.render_user_prompt(
            trip_title="Japan Adventure",
            destination_names=["Tokyo"],
            itinerary=self.itinerary,
        )

        assert "Senso-ji Temple" in rendered
        assert "Akihabara" in rendered
        assert "Ueno Park" in rendered

    def test_is_deterministic(self):
        first = self.prompt.render_user_prompt(
            trip_title="Japan Adventure",
            destination_names=["Tokyo"],
            itinerary=self.itinerary,
        )

        second = self.prompt.render_user_prompt(
            trip_title="Japan Adventure",
            destination_names=["Tokyo"],
            itinerary=self.itinerary,
        )

        assert first == second