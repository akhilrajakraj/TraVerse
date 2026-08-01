"""
Models for the Destinations application.
"""

from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class Destination(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Represents a travel destination available within the platform.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
    )

    country = models.CharField(
        max_length=100,
    )

    city = models.CharField(
        max_length=100,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
    )

    image_url = models.URLField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "destinations"

        verbose_name = "Destination"

        verbose_name_plural = "Destinations"

        ordering = [
            "country",
            "city",
            "name",
        ]

    def __str__(self):
        """
        Return the destination name.
        """

        return self.name