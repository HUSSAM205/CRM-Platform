import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_permission
from app.core.config import get_settings
from app.core.permissions import Permissions
from app.core.rate_limit import limiter
from app.core.security import create_token, decode_token, hash_password, hash_token, verify_password
from app.db.session import get_db
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.auth import (
    AcceptInvitationRequest,
    InvitationPreview,
    InviteRequest,
    InviteResponse,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.user import UserRead
from app.services import audit_service
from app.services.auth_service import user_to_read

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
INVITATION_TTL_DAYS = 7


def _slugify(name: str) -> str:
    slug = "-".join(name.strip().lower().split())
    slug = "".join(c for c in slug if c.isalnum() or c == "-").strip("-")
    return slug or "org"


def _unique_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug = base
    suffix = 1
    while db.scalar(select(Organization).where(Organization.slug == slug)) is not None:
        suffix += 1
        slug = f"{base}-{suffix}"
    return slug


def _set_session_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    is_prod = settings.environment != "development"
    response.set_cookie(
        ACCESS_COOKIE, access_token, httponly=True, secure=is_prod, samesite="strict",
        max_age=settings.access_token_expire_minutes * 60, path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token, httponly=True, secure=is_prod, samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth",
    )
    response.set_cookie(
        CSRF_COOKIE, secrets.token_urlsafe(32), httponly=False, secure=is_prod, samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400, path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


def _issue_session(db: Session, response: Response, user: User, request: Request) -> None:
    access_token = create_token(str(user.id), "access")
    family_id = uuid.uuid4()
    refresh_token = create_token(str(user.id), "refresh", {"family": str(family_id)})

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        family_id=family_id,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    ))
    db.commit()

    _set_session_cookies(response, access_token, refresh_token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def register(payload: RegisterRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> UserRead:
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    admin_role = db.scalar(select(Role).where(Role.name == "admin", Role.is_system.is_(True)))
    if admin_role is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "System roles are not seeded; run migrations")

    org = Organization(name=payload.organization_name, slug=_unique_slug(db, payload.organization_name))
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=admin_role.id, organization_id=org.id))
    db.flush()
    ip = request.client.host if request.client else None
    audit_service.record(
        db, organization_id=org.id, actor_id=user.id, action="organization.created",
        resource_type="organization", resource_id=org.id, extra={"name": org.name}, ip_address=ip,
    )
    audit_service.record(
        db, organization_id=org.id, actor_id=user.id, action="user.registered",
        resource_type="user", resource_id=user.id, extra={"email": user.email}, ip_address=ip,
    )
    db.commit()
    db.refresh(user)

    _issue_session(db, response, user, request)
    return user_to_read(db, user)


@router.post("/login", response_model=UserRead)
@limiter.limit("10/minute")
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> UserRead:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    audit_service.record(
        db, organization_id=user.organization_id, actor_id=user.id, action="user.login",
        resource_type="user", resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    _issue_session(db, response, user, request)
    return user_to_read(db, user)


@router.post("/refresh", response_model=UserRead)
def refresh(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> UserRead:
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_token(refresh_token, "refresh")
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    token_row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    if not token_row:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session")

    now = datetime.now(timezone.utc)
    if token_row.revoked_at is not None or token_row.expires_at < now:
        # Reuse of a revoked/expired token indicates possible theft: kill the whole family.
        db.query(RefreshToken).filter(
            RefreshToken.family_id == token_row.family_id, RefreshToken.revoked_at.is_(None)
        ).update({"revoked_at": now})
        db.commit()
        _clear_session_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session revoked, please log in again")

    user = db.get(User, token_row.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    new_access = create_token(str(user.id), "access")
    new_refresh = create_token(str(user.id), "refresh", {"family": str(token_row.family_id)})
    new_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        family_id=token_row.family_id,
        issued_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_row)
    db.flush()

    token_row.revoked_at = now
    token_row.replaced_by_id = new_row.id
    db.commit()

    _set_session_cookies(response, new_access, new_refresh)
    return user_to_read(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> None:
    if refresh_token:
        row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
        if row and row.revoked_at is None:
            row.revoked_at = datetime.now(timezone.utc)
            db.commit()

    _clear_session_cookies(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": datetime.now(timezone.utc)})
    audit_service.record(
        db, organization_id=current_user.organization_id, actor_id=current_user.id,
        action="user.logout_all", resource_type="user", resource_id=current_user.id,
    )
    db.commit()


@router.post("/invitations", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.USER_INVITE)),
) -> InviteResponse:
    role = db.scalar(select(Role).where(Role.name == payload.role_name, Role.is_system.is_(True)))
    if role is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")

    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists")

    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        organization_id=current_user.organization_id,
        email=payload.email,
        role_id=role.id,
        invited_by=current_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITATION_TTL_DAYS),
    )
    db.add(invitation)
    db.flush()
    audit_service.record(
        db, organization_id=current_user.organization_id, actor_id=current_user.id,
        action="invitation.created", resource_type="invitation", resource_id=invitation.id,
        extra={"email": invitation.email, "role": role.name},
    )
    db.commit()

    # No email service is wired up yet, so the invite link is handed back directly for
    # the inviting admin to share manually. Swap for a real email send in a later phase.
    return InviteResponse(invite_url=f"/invite/{token}", token=token, expires_at=invitation.expires_at)


@router.get("/invitations/{token}", response_model=InvitationPreview)
def preview_invitation(token: str, db: Session = Depends(get_db)) -> InvitationPreview:
    invitation = db.scalar(select(Invitation).where(Invitation.token == token))
    if not invitation or invitation.accepted_at is not None or invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found or expired")

    org = db.get(Organization, invitation.organization_id)
    role = db.get(Role, invitation.role_id)
    return InvitationPreview(
        organization_name=org.name, email=invitation.email, role_name=role.name, expires_at=invitation.expires_at
    )


@router.post("/invitations/{token}/accept", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def accept_invitation(
    token: str, payload: AcceptInvitationRequest, response: Response, request: Request, db: Session = Depends(get_db)
) -> UserRead:
    invitation = db.scalar(select(Invitation).where(Invitation.token == token))
    if not invitation or invitation.accepted_at is not None or invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invitation not found or expired")

    if db.scalar(select(User).where(User.email == invitation.email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists")

    user = User(
        organization_id=invitation.organization_id,
        email=invitation.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
        is_email_verified=True,
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=invitation.role_id, organization_id=invitation.organization_id))
    invitation.accepted_at = datetime.now(timezone.utc)
    audit_service.record(
        db, organization_id=invitation.organization_id, actor_id=user.id, action="user.joined",
        resource_type="user", resource_id=user.id, extra={"via_invitation_id": str(invitation.id)},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)

    _issue_session(db, response, user, request)
    return user_to_read(db, user)
