"""
Packing Agent Prompt Version 1.

This prompt instructs the LLM to generate a structured travel packing list
using the validated itinerary, weather forecast and trip information.

The output MUST conform to PackingListSchema.
"""

from __future__ import annotations

from ai.agents.schemas import (
    ItineraryPlanSchema,
    WeatherForecastSchema,
)


class PackingAgentPromptV1:
    """
    Prompt builder for the Packing Agent.
    """

    VERSION = "v1"

    NAME = "packing-agent-v1"

    SYSTEM_PROMPT = """
You are an expert travel packing assistant.

Your responsibility is to generate a practical packing checklist using:

- the travel itinerary
- the expected weather
- trip duration
- traveler information

Return ONLY valid JSON.

Do NOT include markdown.

Do NOT include explanations.

Do NOT include commentary.

Do NOT include code fences.

The JSON MUST exactly match PackingListSchema.

Every packing item MUST contain ALL of the following fields:

- category
- item
- quantity
- reason

Do not invent additional fields.

{
  "items": [
    {
      "category": "clothing",
      "item": "Rain Jacket",
      "quantity": 1,
      "reason": "Expected rain during the trip."
    }
  ]
}

Allowed categories are ONLY:

- clothing
- toiletries
- electronics
- documents
- medication
- accessories
- miscellaneous

Rules:

1. Return at least one packing item.

2. quantity must be between 1 and 20.

3. Do not generate duplicate items.

4. Consider trip duration.

5. Consider expected weather.

6. Consider planned activities.

7. Consider traveler count.

8. Provide a short reason explaining why every item is recommended.

9. Do not include unnecessary luxury items.

10. Every item MUST include a concise human-readable reason.

11. Output JSON only.
""".strip()

    def render_user_prompt(
        self,
        *,
        trip_title: str,
        destination_names: list[str],
        start_date: str,
        end_date: str,
        traveler_count: int,
        trip_notes: str,
        itinerary: ItineraryPlanSchema,
        weather_forecast: WeatherForecastSchema,
    ) -> str:
        """
        Render the Packing Agent prompt from validated planning data.
        """

        notes = trip_notes.strip() or "No additional notes."

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

        weather_lines: list[str] = []

        for day in weather_forecast.days:

            weather_lines.append(
                f"{day.date}: "
                f"{day.condition}, "
                f"High {day.high_f}°F, "
                f"Low {day.low_f}°F, "
                f"{day.precipitation_chance}% precipitation"
            )

        return f"""
Trip Title:
{trip_title}

Destinations:
{", ".join(destination_names)}

Travel Dates:
{start_date} → {end_date}

Traveler Count:
{traveler_count}

Trip Notes:
{notes}

Travel Itinerary:

{chr(10).join(itinerary_lines)}

Weather Forecast:

{chr(10).join(weather_lines)}

Generate a complete travel packing checklist.

Use every piece of available information when deciding what items should be packed.

Return ONLY JSON.
""".strip()


packing_agent_prompt_v1 = PackingAgentPromptV1()