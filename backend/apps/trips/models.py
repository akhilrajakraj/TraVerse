from django.conf import settings
from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class TripStatus(models.TextChoices):
    """
    Lifecycle states for a trip.
    """

    DRAFT = "draft", "Draft"

    PLANNING = (
        "planning",
        "AI Planning In Progress",
    )

    PLANNED = "planned", "Planned"

    COMPLETED = "completed", "Completed"

    CANCELLED = "cancelled", "Cancelled"


class Trip(
    UUIDPrimaryKeyModel,
    TimeStampedModel,
):
    """
    Central travel entity for the platform.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips",
    )

    destinations = models.ManyToManyField(
        "destinations.Destination",
        related_name="trips",
        blank=True,
    )

    title = models.CharField(
        max_length=200,
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=TripStatus.choices,
        default=TripStatus.DRAFT,
        db_index=True,
    )

    traveler_count = models.PositiveSmallIntegerField(
        default=1,
    )

    notes = models.TextField(
        blank=True,
    )

    computed_budget_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "status",
                ],
            ),
        ]

        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    end_date__gte=models.F(
                        "start_date",
                    ),
                ),
                name="trip_end_date_gte_start_date",
            ),
        ]

        verbose_name = "Trip"

        verbose_name_plural = "Trips"

    def __str__(self) -> str:
        return (
            f"{self.title} "
            f"({self.user.email})"
        )

    @property
    def duration_days(self) -> int:
        """
        Inclusive trip duration.
        """

        return (
            self.end_date -
            self.start_date
        ).days + 1