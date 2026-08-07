"""
Builds structured trip context for AI agents.

This module converts Django Trip models into a deterministic,
human-readable context block that can be injected into prompts.
"""

from __future__ import annotations

from typing import List

from apps.trips.models import Trip


class TripContextBuilder:
    """
    Builds textual context describing a trip.

    The output is deterministic so prompts remain stable,
    cacheable and easy to test.
    """

    @classmethod
    def build(
        cls,
        *,
        trip: Trip,
    ) -> str:
        """
        Return a formatted context block for a trip.
        """

        sections: List[str] = [
            cls._trip_information(trip),
            cls._destinations(trip),
            cls._budget(trip),
            cls._weather(trip),
            cls._itinerary(trip),
            cls._recommendations(trip),
            cls._packing(trip),
        ]

        return "\n\n".join(
            section
            for section in sections
            if section.strip()
        )

    # ----------------------------------------------------------
    # Trip
    # ----------------------------------------------------------

    @staticmethod
    def _trip_information(
        trip: Trip,
    ) -> str:

        lines = [
            "=== TRIP ===",
            f"Title: {trip.title}",
        ]

        if getattr(trip, "description", ""):
            lines.append(
                f"Description: {trip.description}"
            )

        if getattr(trip, "start_date", None):
            lines.append(
                f"Start Date: {trip.start_date}"
            )

        if getattr(trip, "end_date", None):
            lines.append(
                f"End Date: {trip.end_date}"
            )

        if getattr(trip, "status", None):
            lines.append(
                f"Status: {trip.status}"
            )

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Destinations
    # ----------------------------------------------------------

    @staticmethod
    def _destinations(
        trip: Trip,
    ) -> str:

        if not hasattr(trip, "destinations"):
            return ""

        queryset = trip.destinations.all()

        if not queryset.exists():
            return ""

        lines = [
            "=== DESTINATIONS ===",
        ]

        for destination in queryset:

            country = getattr(
                destination,
                "country",
                "",
            )

            city = getattr(
                destination,
                "city",
                "",
            )

            if city and country:
                lines.append(
                    f"- {city}, {country}"
                )
            elif city:
                lines.append(
                    f"- {city}"
                )
            else:
                lines.append(
                    f"- {destination}"
                )

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Budget
    # ----------------------------------------------------------

    @staticmethod
    def _budget(
        trip: Trip,
    ) -> str:

        if not hasattr(
            trip,
            "budget",
        ):
            return ""

        try:
            budget = trip.budget
        except Exception:
            return ""

        lines = [
            "=== BUDGET ===",
        ]

        for field in (
            "currency",
            "total_budget",
            "estimated_cost",
            "remaining_budget",
        ):

            if hasattr(
                budget,
                field,
            ):

                value = getattr(
                    budget,
                    field,
                )

                if value not in (
                    None,
                    "",
                ):
                    label = field.replace(
                        "_",
                        " ",
                    ).title()

                    lines.append(
                        f"{label}: {value}"
                    )

        return "\n".join(lines)
    
    # ----------------------------------------------------------
    # Weather
    # ----------------------------------------------------------

    @staticmethod
    def _weather(
        trip: Trip,
    ) -> str:
        """
        Build a weather summary for the trip itinerary.
        """

        if not hasattr(
            trip,
            "itinerary_days",
        ):
            return ""

        queryset = (
            trip.itinerary_days
            .all()
            .order_by("day_number")
        )

        if not queryset.exists():
            return ""

        lines = [
            "=== WEATHER ===",
        ]

        has_weather = False

        for day in queryset:

            if not getattr(
                day,
                "weather_condition",
                None,
            ):
                continue

            has_weather = True

            line = (
                f"Day {day.day_number}: "
                f"{day.weather_condition}"
            )

            low = getattr(
                day,
                "weather_low_f",
                None,
            )

            high = getattr(
                day,
                "weather_high_f",
                None,
            )

            precipitation = getattr(
                day,
                "weather_precipitation_chance",
                None,
            )

            if low is not None and high is not None:
                line += f" ({low}°F–{high}°F)"

            if precipitation is not None:
                line += f", {precipitation}% precipitation"

            lines.append(line)

        if not has_weather:
            return ""

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Itinerary
    # ----------------------------------------------------------

    @staticmethod
    def _itinerary(
        trip: Trip,
    ) -> str:

        if not hasattr(
            trip,
            "itinerary_days",
        ):
            return ""

        queryset = (
            trip.itinerary_days
            .all()
            .order_by(
                "day_number",
            )
        )

        if not queryset.exists():
            return ""

        lines = [
            "=== ITINERARY ===",
        ]

        for day in queryset:

            line = f"Day {day.day_number}"

            if getattr(
                day,
                "date",
                None,
            ):
                line += f" ({day.date})"

            lines.append(line)

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Recommendations
    # ----------------------------------------------------------

    @staticmethod
    def _recommendations(
        trip: Trip,
    ) -> str:

        if not hasattr(
            trip,
            "recommendations",
        ):
            return ""

        queryset = (
            trip.recommendations
            .all()[:10]
        )

        if not queryset.exists():
            return ""

        lines = [
            "=== RECOMMENDATIONS ===",
        ]

        for recommendation in queryset:

            title = getattr(
                recommendation,
                "title",
                str(recommendation),
            )

            lines.append(
                f"- {title}"
            )

        return "\n".join(lines)

    # ----------------------------------------------------------
    # Packing
    # ----------------------------------------------------------

    @staticmethod
    def _packing(
        trip: Trip,
    ) -> str:

        if not hasattr(
            trip,
            "packing_items",
        ):
            return ""

        queryset = (
            trip.packing_items
            .all()
        )

        if not queryset.exists():
            return ""

        lines = [
            "=== PACKING ===",
        ]

        for item in queryset:

            status = (
                "✓"
                if getattr(
                    item,
                    "is_packed",
                    False,
                )
                else "•"
            )

            lines.append(
                f"{status} {item.item}"
            )

        return "\n".join(lines)