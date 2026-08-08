import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    extra: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Append an audit_log row. Never updated or deleted once written.

    Call this from inside service/route functions right alongside the mutation itself
    (same transaction, committed together) so an audited action and its log entry can
    never drift apart.
    """
    entry = AuditLog(
        organization_id=organization_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        extra=extra or {},
        ip_address=ip_address,
    )
    db.add(entry)
    db.flush()
    return entry
