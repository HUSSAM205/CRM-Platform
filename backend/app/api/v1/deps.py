import uuid
from collections.abc import Callable

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.document import Document, DocumentShare
from app.models.role import UserRole
from app.models.user import User
from app.services.permission_service import get_user_permissions

DOCUMENT_PERMISSION_RANK = {"view": 0, "comment": 1, "edit": 2, "manage": 3}


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    if not access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    payload = decode_token(access_token, "access")
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    return user


def require_permission(permission_code: str) -> Callable[..., User]:
    """Dependency factory: 403s unless the current user's roles grant `permission_code`.

    This is the coarse, org-tier role gate. Resource-level checks (e.g. does this
    user have access to this specific document) are layered on top starting Phase 2.
    """

    def _dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if permission_code not in get_user_permissions(db, current_user):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return current_user

    return _dependency


def get_document_permission(db: Session, current_user: User, document: Document) -> str | None:
    """Highest permission level `current_user` has on `document`, or None for no access.

    The document's creator always has 'manage'. Everyone else needs an explicit
    document_shares grant, either to their user id directly or to one of their roles.
    """
    if document.created_by == current_user.id:
        return "manage"

    user_role_ids = [row[0] for row in db.query(UserRole.role_id).filter(UserRole.user_id == current_user.id).all()]

    shares = (
        db.query(DocumentShare)
        .filter(
            DocumentShare.document_id == document.id,
            or_(
                and_(DocumentShare.grantee_type == "user", DocumentShare.grantee_id == current_user.id),
                and_(DocumentShare.grantee_type == "role", DocumentShare.grantee_id.in_(user_role_ids or [uuid.uuid4()])),
            ),
        )
        .all()
    )
    if not shares:
        return None

    best = max(shares, key=lambda s: DOCUMENT_PERMISSION_RANK.get(s.permission, -1))
    return best.permission


def require_document_access(min_permission: str) -> Callable[..., Document]:
    """Resource-level gate layered on top of require_permission for a specific document.

    Composed alongside require_permission(document.*) on document routes: the coarse
    role gate confirms the org-tier capability exists at all, this confirms the user
    can act on *this* document specifically.
    """

    def _dependency(
        document_id: uuid.UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Document:
        document = db.get(Document, document_id)
        if not document or document.organization_id != current_user.organization_id or document.is_deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

        permission = get_document_permission(db, current_user, document)
        if permission is None or DOCUMENT_PERMISSION_RANK[permission] < DOCUMENT_PERMISSION_RANK[min_permission]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to this document")

        return document

    return _dependency
