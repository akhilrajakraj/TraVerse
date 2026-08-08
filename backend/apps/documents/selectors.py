from __future__ import annotations

from apps.documents.models import Document


def get_active_document_by_token(
    *,
    token: str,
) -> Document | None:
    """
    Return an active shared document matching the supplied token.

    Expired and revoked links are excluded from the result.
    """

    document = (
        Document.objects
        .select_related("trip")
        .filter(
            share_token=token,
            is_active=True,
        )
        .first()
    )

    if document is None:
        return None

    if not document.is_valid:
        return None

    return document