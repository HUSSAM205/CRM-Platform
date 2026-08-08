from fastapi import APIRouter

from app.api.v1 import audit, auth, comments, dashboard, documents, health, messages, notifications, search, users, ws

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)
api_router.include_router(comments.router)
api_router.include_router(messages.router)
api_router.include_router(notifications.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
api_router.include_router(search.router)
api_router.include_router(ws.router)

# Additional routers (roles, admin/*) are registered here as each
# implementation phase lands.
