import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import require_permission
from app.core.permissions import Permissions
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_log(
    actor_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.AUDIT_VIEW)),
) -> list[AuditLogRead]:
    stmt = select(AuditLog).where(AuditLog.organization_id == current_user.organization_id)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)
    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)

    entries = db.scalars(stmt).all()
    actor_ids = {e.actor_id for e in entries if e.actor_id}
    actors = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(actor_ids or [uuid.uuid4()])).all()}

    return [
        AuditLogRead(
            id=e.id,
            actor_id=e.actor_id,
            actor_name=actors.get(e.actor_id, "System") if e.actor_id else "System",
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            extra=e.extra,
            ip_address=e.ip_address,
            created_at=e.created_at,
        )
        for e in entries
    ]
