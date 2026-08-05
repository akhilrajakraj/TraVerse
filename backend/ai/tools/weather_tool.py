"""
Deterministic weather lookup tool.

This module provides a predictable seasonal weather estimate that can be
used by the Weather Agent during planning.

The implementation intentionally avoids external weather APIs so that:

- unit tests remain deterministic
- CI never depends on internet connectivity
- no API keys are required
- LLM tool calling can be demonstrated consistently
"""

from __future__ import annotations

from datetime import date


SEASONAL_WEATHER = {
    "winter": {
        "condition": "Cool",
        "high_f": 55,
        "low_f": 40,
        "precipitation_chance": 20,
    },
    "spring": {
        "condition": "Mild",
        "high_f": 68,
        "low_f": 52,
        "precipitation_chance": 30,
    },
    "summer": {
        "condition": "Warm",
        "high_f": 86,
        "low_f": 70,
        "precipitation_chance": 35,
    },
    "autumn": {
        "condition": "Pleasant",
        "high_f": 72,
        "low_f": 56,
        "precipitation_chance": 25,
    },
}

def _season_for_month(
    month: int,
) -> str:
    """
    Determine the meteorological season.

    Northern hemisphere seasons are intentionally used because
    this tool provides approximate travel planning guidance rather
    than real-time forecasts.
    """

    if month in (12, 1, 2):
        return "winter"

    if month in (3, 4, 5):
        return "spring"

    if month in (6, 7, 8):
        return "summer"

    return "autumn"

def get_typical_weather(
    *,
    destination: str,
    travel_date: date,
) -> dict:
    """
    Return a deterministic seasonal weather estimate.

    Parameters
    ----------
    destination:
        Destination name.

    travel_date:
        Travel date.

    Returns
    -------
    dict
        Seasonal weather estimate.
    """

    season = _season_for_month(
        travel_date.month,
    )

    weather = SEASONAL_WEATHER[season]

    return {
        "destination": destination,
        "date": travel_date.isoformat(),
        "season": season,
        **weather,
    }