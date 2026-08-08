import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.deps import get_document_permission, require_permission
from app.api.v1.documents import accessible_documents_stmt
from app.core.permissions import Permissions
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentListItem

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[DocumentListItem])
def search_documents(
    q: str | None = None,
    owner_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_VIEW)),
) -> list[DocumentListItem]:
    stmt = accessible_documents_stmt(db, current_user)
    if q:
        stmt = stmt.where(Document.search_vector.op("@@")(func.websearch_to_tsquery("english", q)))
    if owner_id:
        stmt = stmt.where(Document.created_by == owner_id)
    if date_from:
        stmt = stmt.where(Document.updated_at >= date_from)
    if date_to:
        stmt = stmt.where(Document.updated_at <= date_to)
    stmt = stmt.order_by(Document.updated_at.desc()).limit(100)

    documents = db.scalars(stmt).all()
    return [
        DocumentListItem(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            created_by=doc.created_by,
            updated_at=doc.updated_at,
            mime_type=doc.current_version.mime_type if doc.current_version else None,
            size_bytes=doc.current_version.size_bytes if doc.current_version else None,
            my_permission=get_document_permission(db, current_user, doc) or "view",
        )
        for doc in documents
    ]
