import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
