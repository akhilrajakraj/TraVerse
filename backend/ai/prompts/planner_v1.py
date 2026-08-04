"""
Version 1 Travel Planner prompt.

This module defines the first production prompt used by the
TraVerse AI Travel Planner Agent.

The prompt layer is responsible only for prompt construction.
It remains completely independent of Django models and any
specific LLM provider.
"""

from __future__ import annotations

from ai.prompts.base import PromptTemplate


class TravelPlannerPromptV1(PromptTemplate):
    """
    Version 1 Travel Planner prompt.

    This prompt instructs the LLM to generate a structured travel
    itinerary matching the ItineraryPlanSchema defined within the
    AI infrastructure.

    The prompt intentionally remains provider-independent.
    """

    def __init__(self) -> None:
        super().__init__(
            name="travel_planner",
            version=1,
            system_prompt=(
                "You are an expert travel planner.\n\n"
                "Your responsibility is to generate realistic, practical, "
                "and well-balanced travel itineraries.\n\n"
                "Your response MUST strictly follow the required JSON schema.\n\n"
                "Rules:\n"
                "- Return valid JSON only.\n"
                "- Do not return Markdown.\n"
                "- Do not use code fences.\n"
                "- Do not include explanations.\n"
                "- Do not include comments.\n"
                "- Do not invent additional fields.\n"
                "- Every itinerary day must contain one or more itinerary items.\n"
                "- Activities should follow a realistic chronological order.\n"
                "- Estimated costs must be non-negative.\n"
                "- Descriptions should be concise but informative."
            ),
        )

    def render_user_prompt(
        self,
        *,
        trip_title: str,
        destination_names: list[str],
        start_date: str,
        end_date: str,
        traveler_count: int,
        trip_notes: str,
    ) -> str:
        """
        Render the user prompt for itinerary generation.
        """

        destinations = ", ".join(
            destination_names,
        )

        notes = (
            trip_notes.strip()
            if trip_notes and trip_notes.strip()
            else "No additional travel preferences were provided."
        )

        return (
            "Generate a complete travel itinerary.\n\n"
            f"Trip Title: {trip_title}\n"
            f"Destinations: {destinations}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n"
            f"Number of Travelers: {traveler_count}\n"
            f"Trip Notes: {notes}\n\n"
            "Requirements:\n"
            "- Generate an itinerary covering every day of the trip.\n"
            "- Consider the number of travelers when planning activities.\n"
            "- Use the trip notes as traveler preferences whenever possible.\n"
            "- Keep travel time practical.\n"
            "- Include realistic sightseeing, food, transportation and rest.\n"
            "- Include estimated costs when appropriate.\n"
            "- Return ONLY valid JSON matching the required itinerary schema."
        )


travel_planner_prompt_v1 = TravelPlannerPromptV1()