import hashlib
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_document_permission, require_document_access, require_permission
from app.core.permissions import Permissions
from app.db.session import get_db
from app.models.document import Document, DocumentShare, DocumentVersion
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.document import (
    DocumentListItem,
    DocumentRead,
    DocumentShareRead,
    DocumentShareRequest,
    DocumentUpdateRequest,
    DocumentVersionRead,
)
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25MB


def _document_to_read(db: Session, document: Document, current_user: User) -> DocumentRead:
    permission = get_document_permission(db, current_user, document) or "view"
    return DocumentRead(
        id=document.id,
        organization_id=document.organization_id,
        title=document.title,
        description=document.description,
        created_by=document.created_by,
        created_at=document.created_at,
        updated_at=document.updated_at,
        current_version=(
            DocumentVersionRead.model_validate(document.current_version) if document.current_version else None
        ),
        my_permission=permission,
    )


def _accessible_documents_stmt(db: Session, current_user: User):
    role_ids = select(UserRole.role_id).where(UserRole.user_id == current_user.id).scalar_subquery()
    accessible_ids = select(DocumentShare.document_id).where(
        or_(
            and_(DocumentShare.grantee_type == "user", DocumentShare.grantee_id == current_user.id),
            and_(DocumentShare.grantee_type == "role", DocumentShare.grantee_id.in_(role_ids)),
        )
    )
    return select(Document).where(
        Document.organization_id == current_user.organization_id,
        Document.is_deleted.is_(False),
        or_(Document.created_by == current_user.id, Document.id.in_(accessible_ids)),
    )


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(..., min_length=1, max_length=500),
    description: str | None = Form(default=None, max_length=2000),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_CREATE)),
) -> DocumentRead:
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds the 25MB upload limit")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")

    document = Document(
        organization_id=current_user.organization_id,
        title=title,
        description=description,
        created_by=current_user.id,
    )
    db.add(document)
    db.flush()

    storage_key = f"org/{current_user.organization_id}/documents/{document.id}/{uuid.uuid4()}/{file.filename}"
    await get_storage_service().put(storage_key, data)

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        storage_key=storage_key,
        original_filename=file.filename or "untitled",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        checksum_sha256=hashlib.sha256(data).hexdigest(),
        uploaded_by=current_user.id,
    )
    db.add(version)
    db.flush()

    document.current_version_id = version.id
    db.commit()
    db.refresh(document)

    return _document_to_read(db, document, current_user)


@router.get("", response_model=list[DocumentListItem])
def list_documents(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_VIEW)),
) -> list[DocumentListItem]:
    stmt = _accessible_documents_stmt(db, current_user)
    if q:
        stmt = stmt.where(Document.search_vector.op("@@")(func.websearch_to_tsquery("english", q)))
    stmt = stmt.order_by(Document.updated_at.desc())

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


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_VIEW)),
    document: Document = Depends(require_document_access("view")),
) -> DocumentRead:
    return _document_to_read(db, document, current_user)


@router.get("/{document_id}/download")
def download_document(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    document: Document = Depends(require_document_access("view")),
) -> StreamingResponse:
    if not document.current_version:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This document has no uploaded content yet")

    version = document.current_version
    stream = get_storage_service().get_stream(version.storage_key)
    return StreamingResponse(
        stream,
        media_type=version.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{version.original_filename}"'},
    )


@router.post("/{document_id}/versions", response_model=DocumentRead)
async def upload_new_version(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_EDIT)),
    document: Document = Depends(require_document_access("edit")),
) -> DocumentRead:
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds the 25MB upload limit")
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")

    latest_version_number = db.scalar(
        select(DocumentVersion.version_number)
        .where(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_number.desc())
        .limit(1)
    ) or 0

    storage_key = f"org/{current_user.organization_id}/documents/{document.id}/{uuid.uuid4()}/{file.filename}"
    await get_storage_service().put(storage_key, data)

    version = DocumentVersion(
        document_id=document.id,
        version_number=latest_version_number + 1,
        storage_key=storage_key,
        original_filename=file.filename or "untitled",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        checksum_sha256=hashlib.sha256(data).hexdigest(),
        uploaded_by=current_user.id,
    )
    db.add(version)
    db.flush()

    document.current_version_id = version.id
    db.commit()
    db.refresh(document)

    return _document_to_read(db, document, current_user)


@router.put("/{document_id}", response_model=DocumentRead)
def update_document(
    payload: DocumentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_EDIT)),
    document: Document = Depends(require_document_access("edit")),
) -> DocumentRead:
    if payload.title is not None:
        document.title = payload.title
    if payload.description is not None:
        document.description = payload.description
    db.commit()
    db.refresh(document)
    return _document_to_read(db, document, current_user)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_DELETE)),
    document: Document = Depends(require_document_access("manage")),
) -> None:
    document.is_deleted = True
    db.commit()


def _grantee_label(db: Session, share: DocumentShare) -> str:
    if share.grantee_type == "user":
        user = db.get(User, share.grantee_id)
        return user.full_name if user else "Unknown user"
    role = db.get(Role, share.grantee_id)
    return role.name if role else "Unknown role"


@router.get("/{document_id}/shares", response_model=list[DocumentShareRead])
def list_document_shares(
    db: Session = Depends(get_db),
    document: Document = Depends(require_document_access("manage")),
) -> list[DocumentShareRead]:
    shares = db.scalars(select(DocumentShare).where(DocumentShare.document_id == document.id)).all()
    return [
        DocumentShareRead(
            id=s.id,
            grantee_type=s.grantee_type,
            grantee_id=s.grantee_id,
            grantee_label=_grantee_label(db, s),
            permission=s.permission,
            granted_by=s.granted_by,
            created_at=s.created_at,
        )
        for s in shares
    ]


@router.post("/{document_id}/shares", response_model=DocumentShareRead, status_code=status.HTTP_201_CREATED)
def create_document_share(
    payload: DocumentShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DOCUMENT_SHARE)),
    document: Document = Depends(require_document_access("manage")),
) -> DocumentShareRead:
    if payload.grantee_type == "user":
        grantee = db.get(User, payload.grantee_id)
        if not grantee or grantee.organization_id != current_user.organization_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown user")
    else:
        grantee = db.get(Role, payload.grantee_id)
        if not grantee or (grantee.organization_id is not None and grantee.organization_id != current_user.organization_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")

    existing = db.scalar(
        select(DocumentShare).where(
            DocumentShare.document_id == document.id,
            DocumentShare.grantee_type == payload.grantee_type,
            DocumentShare.grantee_id == payload.grantee_id,
        )
    )
    if existing:
        existing.permission = payload.permission
        share = existing
    else:
        share = DocumentShare(
            document_id=document.id,
            grantee_type=payload.grantee_type,
            grantee_id=payload.grantee_id,
            permission=payload.permission,
            granted_by=current_user.id,
        )
        db.add(share)

    db.commit()
    db.refresh(share)

    return DocumentShareRead(
        id=share.id,
        grantee_type=share.grantee_type,
        grantee_id=share.grantee_id,
        grantee_label=_grantee_label(db, share),
        permission=share.permission,
        granted_by=share.granted_by,
        created_at=share.created_at,
    )


@router.delete("/{document_id}/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_share(
    share_id: uuid.UUID,
    db: Session = Depends(get_db),
    document: Document = Depends(require_document_access("manage")),
) -> None:
    share = db.get(DocumentShare, share_id)
    if not share or share.document_id != document.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")
    db.delete(share)
    db.commit()
