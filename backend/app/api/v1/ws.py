import uuid

from fastapi import APIRouter, Cookie, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, access_token: str | None = Cookie(default=None)) -> None:
    if not access_token:
        await websocket.close(code=4401)
        return

    payload = decode_token(access_token, "access")
    if not payload:
        await websocket.close(code=4401)
        return

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError, TypeError):
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        is_valid = bool(user and user.is_active)
    finally:
        db.close()

    if not is_valid:
        await websocket.close(code=4401)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # Clients don't send anything meaningful yet; this just keeps the
            # connection open and lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(user_id, websocket)
