from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRead
from app.services.permission_service import get_user_permissions, get_user_roles


def user_to_read(db: Session, user: User) -> UserRead:
    return UserRead(
        id=user.id,
        organization_id=user.organization_id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        roles=get_user_roles(db, user),
        permissions=sorted(get_user_permissions(db, user)),
    )
