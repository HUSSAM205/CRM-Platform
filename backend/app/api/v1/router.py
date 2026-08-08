from fastapi import APIRouter

from app.api.v1 import auth, documents, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)

# Additional routers (roles, comments, messages, notifications, audit,
# search, dashboard, admin/*) are registered here as each implementation
# phase lands.
