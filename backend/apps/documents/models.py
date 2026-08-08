import secrets

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel, UUIDPrimaryKeyModel


def _generate_share_token() -> str:
    """
    Generate a security-oriented capability token for public sharing.

    `secrets` is used deliberately instead of `uuid4` because this value
    grants access to a public share endpoint.
    """
    return secrets.token_urlsafe(32)


class Document(UUIDPrimaryKeyModel, TimeStampedModel):
    """
    Represents a shareable trip document link.

    PDF exports are generated on-demand and are not persisted as files.
    """

    trip = models.ForeignKey(
        "trips.Trip",
        on_delete=models.CASCADE,
        related_name="documents",
    )

    share_token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=_generate_share_token,
        help_text=(
            "Public capability token. Deliberately distinct from the "
            "document primary key."
        ),
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Owner can revoke a link by deactivating it.",
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Shared Document Link"
        verbose_name_plural = "Shared Document Links"

    def __str__(self) -> str:
        return f"ShareLink<{self.trip.title}>"

    @property
    def is_valid(self) -> bool:
        if not self.is_active:
            return False

        if self.expires_at and self.expires_at < timezone.now():
            return False

        return True