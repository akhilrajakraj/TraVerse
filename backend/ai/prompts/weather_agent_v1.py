"""
Weather Agent Prompt Version 1.

This prompt instructs the LLM to generate a weather forecast for a
validated travel itinerary. The LLM may use the available weather tool
to retrieve deterministic seasonal weather information.

The output MUST conform to WeatherForecastSchema.
"""

from __future__ import annotations

from ai.agents.schemas import ItineraryPlanSchema


class WeatherAgentPromptV1:
    """
    Prompt builder for the Weather Agent.
    """

    VERSION = "v1"

    NAME = "weather-agent-v1"

    SYSTEM_PROMPT = """
You are an expert travel weather planner.

Your responsibility is to estimate expected weather conditions for each
day of the travel itinerary.

You may use the available weather tool whenever weather information is
required.

Return ONLY valid JSON.

Do NOT include markdown.

Do NOT include explanations.

Do NOT include commentary.

Do NOT include code fences.

The JSON MUST follow this schema:

{
  "days": [
    {
      "date": "2026-07-10",
      "condition": "Warm",
      "high_f": 86,
      "low_f": 70,
      "precipitation_chance": 35
    }
  ]
}

Rules:

1. Return one weather entry for every itinerary day.

2. Every itinerary day must appear exactly once.

3. high_f must be greater than or equal to low_f.

4. precipitation_chance must be between 0 and 100.

5. Keep conditions concise.

6. Do not invent additional fields.

7. Output JSON only.
""".strip()

    def render_user_prompt(
        self,
        *,
        trip_title: str,
        destination_names: list[str],
        itinerary: ItineraryPlanSchema,
    ) -> str:
        """
        Render the user prompt using validated itinerary data.
        """

        itinerary_lines: list[str] = []

        for day in itinerary.days:

            itinerary_lines.append(
                f"Day {day.day_number} ({day.date})"
            )

            itinerary_lines.append(
                f"Summary: {day.summary}"
            )

            for item in day.items:

                itinerary_lines.append(
                    f"- {item.title}: {item.description}"
                )

            itinerary_lines.append("")

        return f"""
Trip Title:
{trip_title}

Destinations:
{", ".join(destination_names)}

Travel Itinerary:

{chr(10).join(itinerary_lines)}

Generate a weather forecast for every itinerary day.

Use the available weather tool whenever weather information is needed.

Return ONLY JSON.
""".strip()


weather_agent_prompt_v1 = WeatherAgentPromptV1()