import uuid

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None
    is_active: bool
    roles: list[str]
    permissions: list[str]

    model_config = {"from_attributes": True}


class OrgMemberRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None
    is_active: bool
    roles: list[str]

    model_config = {"from_attributes": True}
