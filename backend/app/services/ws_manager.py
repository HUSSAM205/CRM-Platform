import asyncio
import uuid
from collections import defaultdict

from fastapi import WebSocket


class WebSocketManager:
    """Tracks live WebSocket connections per user and pushes JSON messages to them.

    Route handlers in this app are sync (plain SQLAlchemy Session) and run in FastAPI's
    threadpool, so they can't `await` a websocket.send directly. send_to_user() is the
    thread-safe entry point: it hands the actual async send off to the main event loop
    via run_coroutine_threadsafe, bound once at app startup (see main.py's lifespan).
    """

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].append(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        if websocket in self._connections.get(user_id, []):
            self._connections[user_id].remove(websocket)

    async def _send_to_user(self, user_id: uuid.UUID, message: dict) -> None:
        for ws in list(self._connections.get(user_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id, ws)

    def send_to_user(self, user_id: uuid.UUID, message: dict) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._send_to_user(user_id, message), self._loop)

    def send_to_users(self, user_ids: list[uuid.UUID], message: dict) -> None:
        for user_id in user_ids:
            self.send_to_user(user_id, message)


ws_manager = WebSocketManager()
