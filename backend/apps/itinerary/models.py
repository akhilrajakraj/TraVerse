"""
Domain models for the Itinerary application.
"""

from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class ItineraryDay(
    UUIDPrimaryKeyModel,
    TimeStampedModel,
):
    """
    One day of a trip's itinerary.

    Each itinerary day belongs to exactly one Trip and represents a
    specific calendar date within that trip.
    """

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="itinerary_days",
    )

    date = models.DateField()

    day_number = models.PositiveSmallIntegerField(
        help_text=(
            "1-indexed day of the trip, kept denormalized alongside "
            "`date` for fast display without recomputing from "
            "trip.start_date every time."
        ),
    )

    summary = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        ordering = [
            "day_number",
        ]

        verbose_name = "Itinerary Day"

        verbose_name_plural = "Itinerary Days"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "trip",
                    "day_number",
                ],
                name="unique_day_number_per_trip",
            ),
            models.UniqueConstraint(
                fields=[
                    "trip",
                    "date",
                ],
                name="unique_date_per_trip",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.trip.title} — "
            f"Day {self.day_number}"
        )


class ItineraryItem(
    UUIDPrimaryKeyModel,
    TimeStampedModel,
):
    """
    A single activity within an itinerary day.

    Each item belongs to exactly one itinerary day and may optionally
    reference a destination.
    """

    day = models.ForeignKey(
        ItineraryDay,
        on_delete=models.CASCADE,
        related_name="items",
    )

    destination = models.ForeignKey(
        "destinations.Destination",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itinerary_items",
        help_text=(
            "Optional. SET_NULL, not CASCADE — "
            "deactivating/removing a destination must never destroy "
            "a user's itinerary item."
        ),
    )

    order = models.PositiveIntegerField(
        default=10,
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    start_time = models.TimeField(
        null=True,
        blank=True,
    )

    estimated_cost_usd = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    is_ai_generated = models.BooleanField(
        default=False,
        help_text=(
            "True for items created by Chapter 12's Travel Planner "
            "Agent, False for items a user added or edited manually. "
            "Allows the API and UI to distinguish AI-generated "
            "activities from user-created activities."
        ),
    )

    class Meta:
        ordering = [
            "order",
        ]

        verbose_name = "Itinerary Item"

        verbose_name_plural = "Itinerary Items"

        indexes = [
            models.Index(
                fields=[
                    "day",
                    "order",
                ],
                name="itinerary_day_order_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.title} "
            f"({self.day})"
        )