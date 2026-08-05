"""
Tests for the deterministic weather lookup tool.
"""

from __future__ import annotations

from datetime import date

from ai.tools.weather_tool import (
    _season_for_month,
    get_typical_weather,
)


class TestSeasonForMonth:
    """
    Verify season determination.
    """

    def test_winter(self):
        assert _season_for_month(1) == "winter"
        assert _season_for_month(2) == "winter"
        assert _season_for_month(12) == "winter"

    def test_spring(self):
        assert _season_for_month(3) == "spring"
        assert _season_for_month(4) == "spring"
        assert _season_for_month(5) == "spring"

    def test_summer(self):
        assert _season_for_month(6) == "summer"
        assert _season_for_month(7) == "summer"
        assert _season_for_month(8) == "summer"

    def test_autumn(self):
        assert _season_for_month(9) == "autumn"
        assert _season_for_month(10) == "autumn"
        assert _season_for_month(11) == "autumn"


class TestTypicalWeather:
    """
    Verify deterministic weather generation.
    """

    def test_returns_expected_structure(self):
        weather = get_typical_weather(
            destination="Tokyo",
            travel_date=date(2026, 7, 10),
        )

        assert weather["destination"] == "Tokyo"
        assert weather["date"] == "2026-07-10"
        assert weather["season"] == "summer"

        assert "condition" in weather
        assert "high_f" in weather
        assert "low_f" in weather
        assert "precipitation_chance" in weather

    def test_same_inputs_produce_same_result(self):
        first = get_typical_weather(
            destination="Paris",
            travel_date=date(2026, 4, 18),
        )

        second = get_typical_weather(
            destination="Paris",
            travel_date=date(2026, 4, 18),
        )

        assert first == second

    def test_different_seasons_return_different_values(self):
        winter = get_typical_weather(
            destination="London",
            travel_date=date(2026, 1, 15),
        )

        summer = get_typical_weather(
            destination="London",
            travel_date=date(2026, 7, 15),
        )

        assert winter["season"] != summer["season"]
        assert winter["condition"] != summer["condition"]

    def test_precipitation_range_is_valid(self):
        weather = get_typical_weather(
            destination="Rome",
            travel_date=date(2026, 9, 20),
        )

        assert 0 <= weather["precipitation_chance"] <= 100