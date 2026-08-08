import uuid
from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    document_count: int
    member_count: int
    comments_last_7_days: int
    messages_last_7_days: int
    unread_notifications: int


class ActivityItem(BaseModel):
    id: uuid.UUID
    actor_name: str
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    extra: dict
    created_at: datetime
