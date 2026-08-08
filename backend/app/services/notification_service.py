import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.ws_manager import ws_manager


def notify(db: Session, user_id: uuid.UUID, type_: str, payload: dict[str, Any]) -> Notification:
    notification = Notification(user_id=user_id, type=type_, payload=payload)
    db.add(notification)
    db.flush()

    ws_manager.send_to_user(
        user_id,
        {
            "kind": "notification",
            "id": str(notification.id),
            "type": notification.type,
            "payload": notification.payload,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
        },
    )
    return notification


def notify_many(db: Session, user_ids: set[uuid.UUID], type_: str, payload: dict[str, Any]) -> None:
    for user_id in user_ids:
        notify(db, user_id, type_, payload)
