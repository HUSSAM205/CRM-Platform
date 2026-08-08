from fastapi import APIRouter

from app.api.v1 import auth, comments, documents, health, messages, notifications, users, ws

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)
api_router.include_router(comments.router)
api_router.include_router(messages.router)
api_router.include_router(notifications.router)
api_router.include_router(ws.router)

# Additional routers (roles, audit, search, dashboard, admin/*) are
# registered here as each implementation phase lands.
