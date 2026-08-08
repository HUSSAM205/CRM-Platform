import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    type: str = Field(pattern="^(direct|channel)$")
    member_ids: list[uuid.UUID] = Field(min_length=1)
    name: str | None = Field(default=None, max_length=255)


class ConversationMemberInfo(BaseModel):
    user_id: uuid.UUID
    full_name: str


class ConversationRead(BaseModel):
    id: uuid.UUID
    type: str
    name: str | None
    members: list[ConversationMemberInfo]
    last_message_preview: str | None
    last_message_at: datetime | None
    unread_count: int


class MessageCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageRead(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    body: str
    created_at: datetime
