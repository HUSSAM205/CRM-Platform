import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    original_filename: str
    mime_type: str
    size_bytes: int
    uploaded_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentShareRead(BaseModel):
    id: uuid.UUID
    grantee_type: str
    grantee_id: uuid.UUID
    grantee_label: str
    permission: str
    granted_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    description: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    current_version: DocumentVersionRead | None
    my_permission: str

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    created_by: uuid.UUID
    updated_at: datetime
    mime_type: str | None
    size_bytes: int | None
    my_permission: str
    match_type: str | None = None  # "keyword" | "semantic", set only by hybrid search


class DocumentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)


class DocumentShareRequest(BaseModel):
    grantee_type: str = Field(pattern="^(user|role)$")
    grantee_id: uuid.UUID
    permission: str = Field(pattern="^(view|comment|edit|manage)$")
