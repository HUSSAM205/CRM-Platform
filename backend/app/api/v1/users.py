from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.user import OrgMemberRead, UserRead
from app.services.auth_service import user_to_read

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> UserRead:
    return user_to_read(db, current_user)


@router.get("", response_model=list[OrgMemberRead])
def list_org_members(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[OrgMemberRead]:
    members = db.scalars(
        select(User).where(User.organization_id == current_user.organization_id).order_by(User.full_name)
    ).all()

    roles_by_user: dict = {}
    role_rows = (
        db.query(UserRole.user_id, Role.name)
        .join(Role, Role.id == UserRole.role_id)
        .filter(UserRole.organization_id == current_user.organization_id)
        .all()
    )
    for user_id, role_name in role_rows:
        roles_by_user.setdefault(user_id, []).append(role_name)

    return [
        OrgMemberRead(
            id=member.id,
            email=member.email,
            full_name=member.full_name,
            avatar_url=member.avatar_url,
            is_active=member.is_active,
            roles=roles_by_user.get(member.id, []),
        )
        for member in members
    ]
