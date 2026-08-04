"""
Tests for the Version 1 Travel Planner prompt.
"""

from __future__ import annotations

from ai.prompts.planner_v1 import (
    TravelPlannerPromptV1,
    travel_planner_prompt_v1,
)


class TestTravelPlannerPromptV1:
    """
    Tests for the production travel planner prompt.
    """

    def test_prompt_metadata(self):
        """
        The prompt should expose stable metadata.
        """

        prompt = TravelPlannerPromptV1()

        assert prompt.name == "travel_planner"
        assert prompt.version == 1

    def test_singleton_instance(self):
        """
        The module should expose a singleton prompt instance.
        """

        assert isinstance(
            travel_planner_prompt_v1,
            TravelPlannerPromptV1,
        )

    def test_system_prompt_contains_required_rules(self):
        """
        The system prompt should contain the critical
        JSON generation instructions.
        """

        prompt = TravelPlannerPromptV1()

        system_prompt = prompt.system_prompt

        assert "Return valid JSON only." in system_prompt
        assert "Do not return Markdown." in system_prompt
        assert "Do not use code fences." in system_prompt
        assert "Do not invent additional fields." in system_prompt
        assert "Estimated costs must be non-negative." in system_prompt

    def test_render_user_prompt(self):
        """
        The rendered prompt should contain every
        trip attribute.
        """

        prompt = TravelPlannerPromptV1()

        rendered = prompt.render_user_prompt(
            trip_title="Japan Tour",
            destination_names=[
                "Kyoto",
                "Osaka",
            ],
            start_date="2026-09-10",
            end_date="2026-09-15",
            traveler_count=2,
            trip_notes="Vegetarian food preferred.",
        )

        assert "Japan Tour" in rendered
        assert "Kyoto, Osaka" in rendered
        assert "2026-09-10" in rendered
        assert "2026-09-15" in rendered
        assert "Number of Travelers: 2" in rendered
        assert "Vegetarian food preferred." in rendered

    def test_blank_notes_use_default_message(self):
        """
        Blank trip notes should be replaced with the
        default message.
        """

        prompt = TravelPlannerPromptV1()

        rendered = prompt.render_user_prompt(
            trip_title="Japan Tour",
            destination_names=[
                "Kyoto",
            ],
            start_date="2026-09-10",
            end_date="2026-09-15",
            traveler_count=1,
            trip_notes="",
        )

        assert (
            "No additional travel preferences were provided."
            in rendered
        )

    def test_whitespace_notes_use_default_message(self):
        """
        Whitespace-only notes should also use the
        default message.
        """

        prompt = TravelPlannerPromptV1()

        rendered = prompt.render_user_prompt(
            trip_title="Japan Tour",
            destination_names=[
                "Kyoto",
            ],
            start_date="2026-09-10",
            end_date="2026-09-15",
            traveler_count=1,
            trip_notes="     ",
        )

        assert (
            "No additional travel preferences were provided."
            in rendered
        )

    def test_multiple_destinations_are_joined(self):
        """
        Destination names should be rendered as a
        comma-separated list.
        """

        prompt = TravelPlannerPromptV1()

        rendered = prompt.render_user_prompt(
            trip_title="Europe Trip",
            destination_names=[
                "Paris",
                "Rome",
                "Berlin",
            ],
            start_date="2026-05-01",
            end_date="2026-05-10",
            traveler_count=4,
            trip_notes="Family vacation",
        )

        assert "Paris, Rome, Berlin" in rendered

    def test_prompt_contains_requirements_section(self):
        """
        The generated prompt should contain all planning
        requirements.
        """

        prompt = TravelPlannerPromptV1()

        rendered = prompt.render_user_prompt(
            trip_title="Japan",
            destination_names=[
                "Tokyo",
            ],
            start_date="2026-09-10",
            end_date="2026-09-15",
            traveler_count=2,
            trip_notes="",
        )

        assert "Requirements:" in rendered
        assert "Generate an itinerary covering every day" in rendered
        assert "Consider the number of travelers" in rendered
        assert "Return ONLY valid JSON" in rendered