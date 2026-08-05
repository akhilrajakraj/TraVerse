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
    
# ==============================================================================
# Budget Estimation Schemas
# ==============================================================================


class BudgetLineItemEstimateSchema(BaseModel):
    """
    Represents one AI-estimated budget line item.

    This schema intentionally remains independent of Django models.
    It is used only inside the AI package before persistence.
    """

    category: str = Field(
        ...,
        pattern=r"^(accommodation|transport|food|activities|shopping|misc)$",
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    estimated_amount: float = Field(
        ...,
        ge=0,
    )

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str,
    ) -> str:
        """
        Prevent blank descriptions.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "description must not be blank."
            )

        return cleaned


class BudgetEstimateSchema(BaseModel):
    """
    Represents the complete AI-generated budget estimate.

    The total budget is intentionally NOT included here.

    Django remains the single source of truth for totals via
    Budget services and model signals.
    """

    line_items: list[BudgetLineItemEstimateSchema] = Field(
        ...,
        min_length=1,
        max_length=50,
    )
    
# ==============================================================================
# Weather Schemas
# ==============================================================================

class DailyWeatherSchema(BaseModel):
    """
    Weather estimate for a single itinerary day.
    """

    date: date

    condition: str = Field(
        ...,
        max_length=50,
    )

    high_f: float

    low_f: float

    precipitation_chance: int = Field(
        ...,
        ge=0,
        le=100,
    )

    @field_validator("low_f")
    @classmethod
    def low_must_not_exceed_high(
        cls,
        value: float,
        info,
    ) -> float:
        """
        Ensure the daily low temperature does not exceed the high.
        """

        high = info.data.get("high_f")

        if high is not None and value > high:
            raise ValueError(
                "low_f must not exceed high_f"
            )

        return value


class WeatherForecastSchema(BaseModel):
    """
    Weather forecast for every itinerary day.
    """

    days: list[DailyWeatherSchema] = Field(
        ...,
        min_length=1,
    )
    
# ==============================================================================
# Recommendation Schemas
# ==============================================================================


class RecommendationItemSchema(BaseModel):
    """
    Represents a single AI-generated travel recommendation.

    This schema intentionally remains independent of Django models.
    Recommendation lifecycle state is managed exclusively by the
    Recommendations application.
    """

    destination: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    category: str = Field(
        ...,
        pattern=(
            r"^(restaurant|attraction|hotel|shopping|"
            r"experience|hidden_gem)$"
        ),
    )

    score: float = Field(
        ...,
        ge=0,
        le=1,
    )

    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    @field_validator("destination")
    @classmethod
    def validate_destination(
        cls,
        value: str,
    ) -> str:
        """
        Prevent blank destination names.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "destination must not be blank."
            )

        return cleaned

    @field_validator("reason")
    @classmethod
    def validate_reason(
        cls,
        value: str,
    ) -> str:
        """
        Prevent blank recommendation reasons.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "reason must not be blank."
            )

        return cleaned


class RecommendationBatchSchema(BaseModel):
    """
    Complete AI-generated recommendation batch.

    Recommendation persistence is handled by the Django
    Recommendations application.
    """

    recommendations: list[RecommendationItemSchema] = Field(
        ...,
        min_length=1,
        max_length=50,
    )