from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class InviteRequest(BaseModel):
    email: EmailStr
    role_name: str = Field(min_length=1, max_length=100)


class InviteResponse(BaseModel):
    invite_url: str
    token: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class InvitationPreview(BaseModel):
    organization_name: str
    email: EmailStr
    role_name: str
    expires_at: datetime
