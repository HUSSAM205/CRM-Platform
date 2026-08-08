import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.deps import get_document_permission, require_permission
from app.api.v1.documents import accessible_documents_stmt
from app.core.permissions import Permissions
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentListItem
from app.services.embedding_service import semantic_search

router = APIRouter(prefix="/search", tags=["search"])


def _to_list_item(db: Session, doc: Document, current_user: User, match_type: str | None) -> DocumentListItem:
    return DocumentListItem(
        id=doc.id,
        title=doc.title,
        description=doc.description,
        created_by=doc.created_by,
        updated_at=doc.updated_at,
        mime_type=doc.current_version.mime_type if doc.current_version else None,
        size_bytes=doc.current_version.size_bytes if doc.current_version else None,
        my_permission=get_document_permission(db, current_user, doc) or "view",
        match_type=match_type,
    )


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
    return [_to_list_item(db, doc, current_user, match_type="keyword" if q else None) for doc in documents]


@router.get("/semantic", response_model=list[DocumentListItem])
def search_semantic(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_VIEW)),
) -> list[DocumentListItem]:
    """Hybrid search: exact keyword matches first, then semantically-similar documents
    that didn't already match on keywords. If the embedding model/service errors out,
    falls back to keyword-only results rather than failing the request - AI is an
    additive layer on top of search, never a hard dependency for it to work at all.
    """
    if not q.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "q is required")

    keyword_stmt = accessible_documents_stmt(db, current_user).where(
        Document.search_vector.op("@@")(func.websearch_to_tsquery("english", q))
    )
    keyword_docs = db.scalars(keyword_stmt).all()
    results = [_to_list_item(db, doc, current_user, match_type="keyword") for doc in keyword_docs]
    seen_ids = {doc.id for doc in keyword_docs}

    try:
        semantic_matches = semantic_search(db, current_user.organization_id, q, limit=20)
    except Exception:
        semantic_matches = []

    if semantic_matches:
        accessible_ids = {doc.id for doc in db.scalars(accessible_documents_stmt(db, current_user)).all()}
        for document_id, _distance in semantic_matches:
            if document_id in seen_ids or document_id not in accessible_ids:
                continue
            doc = db.get(Document, document_id)
            if doc:
                results.append(_to_list_item(db, doc, current_user, match_type="semantic"))
                seen_ids.add(document_id)

    return results
