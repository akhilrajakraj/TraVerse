"""Version 1 Travel Planner prompt."""

from __future__ import annotations

from ai.prompts.base import PromptTemplate
from ai.prompts.sanitization import (
    PROMPT_INJECTION_DEFENSE_INSTRUCTION,
    delimit_user_content,
)


class TravelPlannerPromptV1(PromptTemplate):
    """Version 1 Travel Planner prompt with explicit output contract."""

    def __init__(self) -> None:
        super().__init__(
            name="travel_planner",
            version=1,
            system_prompt=(
                "You are an expert travel planner.\n\n"
                "Your responsibility is to generate realistic, practical, "
                "and well-balanced travel itineraries.\n\n"
                "The required output is ONE JSON OBJECT representing an itinerary. "
                "The top-level object MUST contain a `days` array.\n\n"
                "Required output shape:\n"
                "{\n"
                '  "days": [\n'
                "    {\n"
                '      "day_number": 1,\n'
                '      "date": "YYYY-MM-DD",\n'
                '      "summary": "Short description of the day",\n'
                '      "items": [\n'
                "        {\n"
                '          "title": "Activity title",\n'
                '          "description": "Concise activity description",\n'
                '          "start_time": "HH:MM:SS",\n'
                '          "estimated_cost_usd": 25.0\n'
                "        }\n"
                "      ]\n"
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                "- Return exactly ONE JSON OBJECT; never return an array at the top level.\n"
                "- The top-level object MUST contain `days`.\n"
                "- Do not return `tripTitle`, `trip_title`, `cost`, `hotel`, or any other unsupported top-level field.\n"
                "- Every day MUST contain `day_number`, `date`, `summary`, and `items`.\n"
                "- Every itinerary item MUST contain `title`, `description`, `start_time`, and `estimated_cost_usd`.\n"
                "- Use null for `start_time` or `estimated_cost_usd` when a value cannot be estimated.\n"
                "- Every itinerary day must contain one or more itinerary items.\n"
                "- Activities should follow a realistic chronological order.\n"
                "- Estimated costs must be non-negative when present.\n"
                "- Descriptions should be concise but informative.\n"
                "- Do not return the JSON Schema itself, `$defs`, field definitions, or schema metadata.\n"
                "- Do not return Markdown, code fences, comments, or explanations."
                + PROMPT_INJECTION_DEFENSE_INSTRUCTION
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
        destinations = ", ".join(destination_names)
        notes = (
            trip_notes.strip()
            if trip_notes and trip_notes.strip()
            else "No additional travel preferences were provided."
        )
        user_content = f"Trip Title: {trip_title}\nTrip Notes: {notes}"

        return (
            "Generate a complete travel itinerary.\n\n"
            f"{delimit_user_content(user_content)}\n"
            f"Destinations: {destinations}\n"
            f"Start Date: {start_date}\n"
            f"End Date: {end_date}\n"
            f"Number of Travelers: {traveler_count}\n\n"
            "Requirements:\n"
            "- Generate an itinerary covering every day of the trip.\n"
            "- Use ISO dates (YYYY-MM-DD) for each day's `date`.\n"
            "- Consider the number of travelers when planning activities.\n"
            "- Use the trip notes as traveler preferences whenever possible.\n"
            "- Keep travel time practical.\n"
            "- Include realistic sightseeing, food, transportation and rest.\n"
            "- Include estimated costs when appropriate.\n"
            "- Return ONLY one JSON object matching the output shape shown above.\n"
            "- Do not return the schema definition itself."
        )


travel_planner_prompt_v1 = TravelPlannerPromptV1()
