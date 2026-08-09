from __future__ import annotations

from apps.core.models import AuditLogEntry


def log_audit_event(
    *,
    user,
    action: str,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> AuditLogEntry:
    """Persist a security-relevant audit event."""
    return AuditLogEntry.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        metadata=metadata or {},
    )
