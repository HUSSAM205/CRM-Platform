from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User


def get_user_permissions(db: Session, user: User) -> set[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user.id)
    )
    return set(db.scalars(stmt).all())


def get_user_roles(db: Session, user: User) -> list[str]:
    stmt = select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
    return list(db.scalars(stmt).all())
