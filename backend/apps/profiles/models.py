"""
Profile model for the TraVerse platform.
"""

from django.conf import settings
from django.db import models

from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class Gender(models.TextChoices):
    """
    Supported gender choices.
    """

    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer Not To Say"


class Profile(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Stores additional information about a user.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
    )

    profile_picture = models.URLField(
        blank=True,
    )

    bio = models.TextField(
        blank=True,
    )

    emergency_contact = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        db_table = "profiles"

        verbose_name = "Profile"

        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"{self.user.email}"