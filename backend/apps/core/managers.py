"""
Shared custom model managers.
"""

from django.db import models


class SoftDeleteManager(models.Manager):
    """
    Default manager for models using SoftDeleteModel.

    Automatically excludes soft-deleted rows from the default queryset.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)