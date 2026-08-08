import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.permissions import Permissions
from app.db.session import get_db
from app.models.messaging import Conversation, ConversationMember, Message
from app.models.user import User
from app.schemas.messaging import (
    ConversationCreateRequest,
    ConversationMemberInfo,
    ConversationRead,
    MessageCreateRequest,
    MessageRead,
)
from app.services.notification_service import notify
from app.services.permission_service import get_user_permissions
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["messages"])


def _require_member(db: Session, conversation_id: uuid.UUID, user: User) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if not conversation or conversation.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    membership = db.get(ConversationMember, {"conversation_id": conversation_id, "user_id": user.id})
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a member of this conversation")
    return conversation


def _conversation_to_read(db: Session, conversation: Conversation, current_user: User) -> ConversationRead:
    members = db.scalars(
        select(ConversationMember).where(ConversationMember.conversation_id == conversation.id)
    ).all()
    member_infos = []
    my_last_read = None
    for m in members:
        if m.user_id == current_user.id:
            my_last_read = m.last_read_at
        user = db.get(User, m.user_id)
        if user:
            member_infos.append(ConversationMemberInfo(user_id=user.id, full_name=user.full_name))

    last_message = db.scalar(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
        .limit(1)
    )

    unread_stmt = select(Message).where(
        Message.conversation_id == conversation.id,
        Message.sender_id != current_user.id,
        Message.deleted_at.is_(None),
    )
    if my_last_read:
        unread_stmt = unread_stmt.where(Message.created_at > my_last_read)
    unread_count = len(db.scalars(unread_stmt).all())

    # For a direct conversation, show the other person's name rather than your own.
    name = conversation.name
    if conversation.type == "direct" and not name:
        other = next((m for m in member_infos if m.user_id != current_user.id), None)
        name = other.full_name if other else "Direct message"

    return ConversationRead(
        id=conversation.id,
        type=conversation.type,
        name=name,
        members=member_infos,
        last_message_preview=last_message.body[:140] if last_message else None,
        last_message_at=last_message.created_at if last_message else None,
        unread_count=unread_count,
    )


@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    member_ids = set(payload.member_ids) | {current_user.id}
    for uid in member_ids:
        member = db.get(User, uid)
        if not member or member.organization_id != current_user.organization_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown user in member list")

    if payload.type == "direct":
        if len(member_ids) != 2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Direct conversations must have exactly 2 members")
        other_id = next(uid for uid in member_ids if uid != current_user.id)
        existing = (
            db.query(Conversation)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .filter(Conversation.type == "direct", Conversation.organization_id == current_user.organization_id)
            .filter(ConversationMember.user_id.in_([current_user.id, other_id]))
            .all()
        )
        for candidate in {c.id: c for c in existing}.values():
            member_rows = db.scalars(
                select(ConversationMember.user_id).where(ConversationMember.conversation_id == candidate.id)
            ).all()
            if set(member_rows) == member_ids:
                return _conversation_to_read(db, candidate, current_user)

    conversation = Conversation(
        organization_id=current_user.organization_id,
        type=payload.type,
        name=payload.name if payload.type == "channel" else None,
        created_by=current_user.id,
    )
    db.add(conversation)
    db.flush()

    now = datetime.now(timezone.utc)
    for uid in member_ids:
        db.add(ConversationMember(conversation_id=conversation.id, user_id=uid, last_read_at=now))

    db.commit()
    db.refresh(conversation)
    return _conversation_to_read(db, conversation, current_user)


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ConversationRead]:
    conversation_ids = db.scalars(
        select(ConversationMember.conversation_id).where(ConversationMember.user_id == current_user.id)
    ).all()
    conversations = db.scalars(select(Conversation).where(Conversation.id.in_(conversation_ids or [uuid.uuid4()]))).all()
    reads = [_conversation_to_read(db, c, current_user) for c in conversations]
    reads.sort(key=lambda r: r.last_message_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return reads


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageRead]:
    _require_member(db, conversation_id, current_user)
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
        .order_by(Message.created_at.asc())
        .limit(200)
    ).all()

    senders = {m.id: db.get(User, m.sender_id) for m in messages}
    return [
        MessageRead(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            sender_name=senders[m.id].full_name if senders[m.id] else "Unknown",
            body=m.body,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post(
    "/conversations/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED
)
def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageRead:
    conversation = _require_member(db, conversation_id, current_user)
    if Permissions.MESSAGE_SEND not in get_user_permissions(db, current_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")

    message = Message(conversation_id=conversation.id, sender_id=current_user.id, body=payload.body)
    db.add(message)
    db.flush()

    membership = db.get(ConversationMember, {"conversation_id": conversation.id, "user_id": current_user.id})
    if membership:
        membership.last_read_at = message.created_at

    other_member_ids = db.scalars(
        select(ConversationMember.user_id).where(
            ConversationMember.conversation_id == conversation.id, ConversationMember.user_id != current_user.id
        )
    ).all()

    read = MessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        sender_name=current_user.full_name,
        body=message.body,
        created_at=message.created_at,
    )

    ws_manager.send_to_users(list(other_member_ids), {"kind": "message", **read.model_dump(mode="json")})

    for uid in other_member_ids:
        notify(
            db,
            uid,
            "message",
            {
                "conversation_id": str(conversation.id),
                "sender_id": str(current_user.id),
                "sender_name": current_user.full_name,
                "snippet": message.body[:140],
            },
        )

    db.commit()
    return read


@router.post("/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_conversation_read(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    _require_member(db, conversation_id, current_user)
    membership = db.get(ConversationMember, {"conversation_id": conversation_id, "user_id": current_user.id})
    if membership:
        membership.last_read_at = datetime.now(timezone.utc)
        db.commit()
