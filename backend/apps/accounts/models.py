"""
Custom User model for the TraVerse platform.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.models import (
    TimeStampedModel,
    UUIDPrimaryKeyModel,
)


class User(UUIDPrimaryKeyModel, TimeStampedModel, AbstractUser):
    """
    Custom user model using email as the primary login identifier.
    """

    username = None

    email = models.EmailField(
        unique=True,
    )

    first_name = models.CharField(
        max_length=150,
    )

    last_name = models.CharField(
        max_length=150,
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email