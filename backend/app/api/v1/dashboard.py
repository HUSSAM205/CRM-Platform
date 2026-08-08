import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.comment import Comment
from app.models.document import Document
from app.models.messaging import Conversation, Message
from app.models.notification import Notification
from app.models.user import User
from app.schemas.dashboard import ActivityItem, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Activity feed is visible to every org member, so only expose non-sensitive action
# types here (no logins/IP addresses/session events - those stay in the admin-only
# /audit-log endpoint).
FEED_ACTIONS = (
    "document.created",
    "document.version_uploaded",
    "document.shared",
    "comment.created",
    "user.joined",
    "invitation.created",
)


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardSummary:
    org_id = current_user.organization_id
    since = datetime.now(timezone.utc) - timedelta(days=7)

    document_count = db.scalar(
        select(func.count()).select_from(Document).where(Document.organization_id == org_id, Document.is_deleted.is_(False))
    ) or 0
    member_count = db.scalar(select(func.count()).select_from(User).where(User.organization_id == org_id)) or 0
    comments_count = (
        db.scalar(
            select(func.count())
            .select_from(Comment)
            .join(Document, Document.id == Comment.document_id)
            .where(Document.organization_id == org_id, Comment.created_at >= since)
        )
        or 0
    )
    messages_count = (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Conversation.organization_id == org_id, Message.created_at >= since)
        )
        or 0
    )
    unread_notifications = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        )
        or 0
    )

    return DashboardSummary(
        document_count=document_count,
        member_count=member_count,
        comments_last_7_days=comments_count,
        messages_last_7_days=messages_count,
        unread_notifications=unread_notifications,
    )


@router.get("/activity-feed", response_model=list[ActivityItem])
def get_activity_feed(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ActivityItem]:
    entries = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == current_user.organization_id, AuditLog.action.in_(FEED_ACTIONS))
        .order_by(AuditLog.created_at.desc())
        .limit(30)
    ).all()

    actor_ids = {e.actor_id for e in entries if e.actor_id}
    actors = {u.id: u.full_name for u in db.query(User).filter(User.id.in_(actor_ids or [uuid.uuid4()])).all()}

    return [
        ActivityItem(
            id=e.id,
            actor_name=actors.get(e.actor_id, "System") if e.actor_id else "System",
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            extra=e.extra,
            created_at=e.created_at,
        )
        for e in entries
    ]
