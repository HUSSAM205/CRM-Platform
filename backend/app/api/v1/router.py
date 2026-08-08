from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)

# Additional routers (auth, users, roles, documents, comments, messages,
# notifications, audit, search, dashboard, admin/*) are registered here as
# each implementation phase lands.
