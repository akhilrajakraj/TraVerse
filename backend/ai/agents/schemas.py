"""
Pydantic schemas for the Travel Planner Agent.

These schemas represent the validated output produced by the first
AI agent in the TraVerse platform.

The schemas intentionally remain independent of Django models and are
used exclusively by the AI infrastructure layer before validated data
crosses into the application layer.
"""

from __future__ import annotations

from datetime import date
from datetime import time

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class ItineraryItemSchema(BaseModel):
    """
    Represents a single itinerary activity.
    """

    title: str = Field(
        ...,
        max_length=200,
    )

    description: str = Field(
        default="",
        max_length=1000,
    )

    start_time: time | None = None

    estimated_cost_usd: float | None = Field(
        default=None,
        ge=0,
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        """
        Prevent blank activity titles.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "title must not be blank."
            )

        return cleaned


class ItineraryDaySchema(BaseModel):
    """
    Represents one travel day.
    """

    day_number: int = Field(
        ...,
        ge=1,
    )

    date: date

    summary: str = Field(
        default="",
        max_length=255,
    )

    items: list[ItineraryItemSchema] = Field(
        ...,
        min_length=1,
        max_length=12,
    )


class ItineraryPlanSchema(BaseModel):
    """
    Represents the complete travel itinerary.
    """

    days: list[ItineraryDaySchema] = Field(
        ...,
        min_length=1,
    )