"""
Recommendation Agent Prompt Version 1.

This prompt instructs the LLM to generate personalized travel
recommendations by combining the validated itinerary, estimated budget,
and weather forecast.

The output MUST conform to RecommendationBatchSchema.
"""

from __future__ import annotations

from ai.agents.schemas import (
    BudgetEstimateSchema,
    ItineraryPlanSchema,
    RecommendationBatchSchema,
    WeatherForecastSchema,
)


class RecommendationAgentPromptV1:
    """
    Prompt builder for the Recommendation Agent.
    """

    VERSION = "v1"

    NAME = "recommendation-agent-v1"

    SYSTEM_PROMPT = """
You are an expert travel recommendation planner.

Your responsibility is to generate high-quality travel
recommendations using:

- the itinerary
- estimated budget
- expected weather

Return ONLY valid JSON.

Do NOT include markdown.

Do NOT include explanations.

Do NOT include commentary.

Do NOT include code fences.

The JSON MUST follow this exact schema:

{
  "recommendations": [
    {
      "destination": "Kyoto",
      "category": "attraction",
      "score": 0.95,
      "reason": "Visit Fushimi Inari early in the morning to avoid crowds."
    }
  ]
}

Allowed categories are ONLY:

- restaurant
- attraction
- hotel
- shopping
- experience
- hidden_gem


Rules:

1. Return at least one recommendation.

2. Score must be between 0 and 1.

3. Do not generate duplicate recommendations.

4. Recommendations should complement—not repeat—the itinerary.

5. Consider weather conditions.

6. Consider estimated budget.

7. Recommendations should be realistic for the destination.

8. Keep reasons concise.

9. Output JSON only.
""".strip()

    def render_user_prompt(
        self,
        *,
        trip_title: str,
        destination_names: list[str],
        trip_notes: str,
        itinerary: ItineraryPlanSchema,
        budget_estimate: BudgetEstimateSchema,
        weather_forecast: WeatherForecastSchema,
    ) -> str:
        """
        Render the Recommendation Agent prompt from validated planning
        data.
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

        budget_lines: list[str] = []

        for item in budget_estimate.line_items:

            budget_lines.append(
                f"- {item.category}: {item.description} "
                f"(${item.estimated_amount})"
            )

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

Trip Notes:
{notes}

Travel Itinerary:

{chr(10).join(itinerary_lines)}

Estimated Budget:

{chr(10).join(budget_lines)}

Weather Forecast:

{chr(10).join(weather_lines)}

Generate personalized travel recommendations.

Use all available information when deciding what to recommend.

Return ONLY JSON.
""".strip()


recommendation_agent_prompt_v1 = RecommendationAgentPromptV1()