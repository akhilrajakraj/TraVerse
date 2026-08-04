"""
Budget Agent Prompt Version 1.

This prompt instructs the LLM to estimate a travel budget based on the
validated itinerary produced by the Travel Planner Agent.

The output MUST conform to BudgetEstimateSchema.
"""

from __future__ import annotations

from ai.agents.schemas import ItineraryPlanSchema


class BudgetAgentPromptV1:
    """
    Prompt builder for the Budget Agent.
    """

    VERSION = "v1"

    NAME = "budget-agent-v1"

    SYSTEM_PROMPT = """
You are an expert travel budget planner.

Your responsibility is to estimate realistic travel expenses for the
provided itinerary.

You MUST return ONLY valid JSON.

Do NOT include markdown.

Do NOT include explanations.

Do NOT include commentary.

Do NOT include code fences.

The JSON MUST follow this exact schema:

{
  "line_items": [
    {
      "category": "accommodation",
      "description": "Hotel for entire stay",
      "estimated_amount": 450.00
    }
  ]
}

Allowed categories are ONLY:

- accommodation
- transport
- food
- activities
- shopping
- misc

Rules:

1. Every amount must be non-negative.

2. Return at least one budget line item.

3. Group similar expenses together.

4. Do NOT generate duplicate categories unless necessary.

5. Estimate realistic costs based on:

- destination
- trip duration
- itinerary
- traveler count

6. Do NOT return a total.

7. Do NOT return currency.

8. Output JSON only.
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
    ) -> str:
        """
        Render the user prompt from validated planning data.
        """

        notes = trip_notes.strip() or "No additional notes."

        itinerary_text: list[str] = []

        for day in itinerary.days:

            itinerary_text.append(
                f"Day {day.day_number} ({day.date})"
            )

            itinerary_text.append(
                f"Summary: {day.summary}"
            )

            for item in day.items:

                itinerary_text.append(
                    f"- {item.title}: {item.description}"
                )

            itinerary_text.append("")

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

{chr(10).join(itinerary_text)}

Estimate a realistic travel budget for this itinerary.

Return ONLY JSON.
""".strip()


budget_agent_prompt_v1 = BudgetAgentPromptV1()