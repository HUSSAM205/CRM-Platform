import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_document_access, require_permission
from app.core.permissions import Permissions
from app.db.session import get_db
from app.models.comment import Comment, CommentMention
from app.models.document import Document
from app.models.user import User
from app.schemas.comment import CommentCreateRequest, CommentRead
from app.services import audit_service
from app.services.notification_service import notify
from app.services.permission_service import get_user_permissions

router = APIRouter(tags=["comments"])


def _comment_to_read(db: Session, comment: Comment) -> CommentRead:
    author = db.get(User, comment.author_id)
    mentioned_ids = [
        row[0] for row in db.query(CommentMention.mentioned_user_id).filter(CommentMention.comment_id == comment.id).all()
    ]
    return CommentRead(
        id=comment.id,
        document_id=comment.document_id,
        parent_comment_id=comment.parent_comment_id,
        author_id=comment.author_id,
        author_name=author.full_name if author else "Unknown",
        body="[deleted]" if comment.is_deleted else comment.body,
        is_edited=comment.is_edited,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        mentioned_user_ids=mentioned_ids,
    )


@router.get("/documents/{document_id}/comments", response_model=list[CommentRead])
def list_comments(
    db: Session = Depends(get_db),
    document: Document = Depends(require_document_access("view")),
) -> list[CommentRead]:
    # Deleted comments are kept as tombstones (body replaced client-side-visibly with
    # "[deleted]") rather than dropped outright, so a reply thread doesn't lose its
    # parent and become orphaned/invisible when the parent comment is removed.
    comments = db.scalars(
        select(Comment).where(Comment.document_id == document.id).order_by(Comment.created_at.asc())
    ).all()
    return [_comment_to_read(db, c) for c in comments]


@router.post("/documents/{document_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(
    payload: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.COMMENT_CREATE)),
    document: Document = Depends(require_document_access("comment")),
) -> CommentRead:
    if payload.parent_comment_id:
        parent = db.get(Comment, payload.parent_comment_id)
        if not parent or parent.document_id != document.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Parent comment not found on this document")

    comment = Comment(
        document_id=document.id,
        parent_comment_id=payload.parent_comment_id,
        author_id=current_user.id,
        body=payload.body,
    )
    db.add(comment)
    db.flush()

    valid_mentions: list[uuid.UUID] = []
    for user_id in set(payload.mentioned_user_ids):
        mentioned_user = db.get(User, user_id)
        if mentioned_user and mentioned_user.organization_id == current_user.organization_id:
            db.add(CommentMention(comment_id=comment.id, mentioned_user_id=user_id))
            valid_mentions.append(user_id)

    # Watchers: the document's creator plus anyone who has previously commented on this
    # thread, minus the author (don't notify yourself) and minus anyone already mentioned
    # (they get the more specific "mention" notification instead).
    prior_authors = set(
        row[0] for row in db.query(Comment.author_id).filter(Comment.document_id == document.id).all()
    )
    watchers = (prior_authors | {document.created_by}) - {current_user.id} - set(valid_mentions)

    notification_payload = {
        "document_id": str(document.id),
        "document_title": document.title,
        "comment_id": str(comment.id),
        "author_id": str(current_user.id),
        "author_name": current_user.full_name,
        "snippet": comment.body[:140],
    }
    for user_id in valid_mentions:
        notify(db, user_id, "mention", notification_payload)
    for user_id in watchers:
        notify(db, user_id, "comment", notification_payload)

    audit_service.record(
        db, organization_id=current_user.organization_id, actor_id=current_user.id, action="comment.created",
        resource_type="document", resource_id=document.id, extra={"comment_id": str(comment.id)},
    )

    db.commit()
    db.refresh(comment)
    return _comment_to_read(db, comment)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    document = db.get(Document, comment.document_id)
    if not document or document.organization_id != current_user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")

    is_own_comment = comment.author_id == current_user.id
    can_delete_any = Permissions.COMMENT_DELETE_ANY in get_user_permissions(db, current_user)
    if not is_own_comment and not can_delete_any:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments")

    comment.is_deleted = True
    audit_service.record(
        db, organization_id=current_user.organization_id, actor_id=current_user.id, action="comment.deleted",
        resource_type="document", resource_id=document.id, extra={"comment_id": str(comment.id)},
    )
    db.commit()
