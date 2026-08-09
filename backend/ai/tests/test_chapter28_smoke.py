"""Chapter 28 real-provider smoke test.

This test is intentionally opt-in and is executed only by the nightly
workflow after its GitHub Actions gate has confirmed that the provider
credential and smoke-test flag are configured.
"""

from __future__ import annotations

import os

from ai.agents.travel_planner import TravelPlannerAgent
from ai.graphs.state import PlanningGraphState


def main() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is required for the real-provider smoke test")

    state: PlanningGraphState = {
        "trip_title": "Chapter 28 Smoke Test",
        "destination_names": ["Kochi"],
        "start_date": "2026-09-01",
        "end_date": "2026-09-03",
        "traveler_count": 2,
        "trip_notes": "Create a concise, practical three-day travel itinerary for smoke testing.",
    }

    result = TravelPlannerAgent().plan(state)
    itinerary = result.get("itinerary")

    if itinerary is None:
        raise AssertionError("TravelPlannerAgent did not return an itinerary")

    if not getattr(itinerary, "days", None):
        raise AssertionError("Provider returned an itinerary without days")

    print(f"AI smoke test passed: received {len(itinerary.days)} itinerary day(s)")


if __name__ == "__main__":
    main()
