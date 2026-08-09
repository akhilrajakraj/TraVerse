from django.db import models

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


class BookingType(models.TextChoices):
    FLIGHT = "flight", "Flight"
    HOTEL = "hotel", "Hotel"
    ACTIVITY = "activity", "Activity"
    OTHER = "other", "Other"


class BookingStatus(models.TextChoices):
    INTENT_ONLY = "intent_only", "Intent Only"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"


class Booking(UUIDPrimaryKeyModel, TimeStampedModel):
    """A user's booking intent; not a confirmed external reservation."""

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    source_recommendation = models.ForeignKey(
        "recommendations.Recommendation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    booking_type = models.CharField(
        max_length=20,
        choices=BookingType.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.INTENT_ONLY,
    )
    title = models.CharField(max_length=200)
    estimated_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Booking Intent"
        verbose_name_plural = "Booking Intents"

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"
