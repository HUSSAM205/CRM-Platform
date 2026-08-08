import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parent_comment_id: uuid.UUID | None = None
    mentioned_user_ids: list[uuid.UUID] = Field(default_factory=list)


class CommentRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    parent_comment_id: uuid.UUID | None
    author_id: uuid.UUID
    author_name: str
    body: str
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    mentioned_user_ids: list[uuid.UUID]
