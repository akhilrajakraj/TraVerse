"""
Shared abstract base models used across every app in the project.

This module defines ZERO concrete (table-backed) models.
"""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model adding created/updated timestamps.

    Every model representing a business entity should inherit from this
    instead of declaring its own timestamp fields.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDPrimaryKeyModel(models.Model):
    """
    Abstract base model using UUID primary keys.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract base model implementing soft deletion.
    """

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()

        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )