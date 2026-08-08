from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.csrf import CSRFMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url=None,
)

# Middleware executes in reverse order of registration (last added = outermost), so
# CORS is added last: it must wrap CSRFMiddleware to handle preflight OPTIONS requests
# and attach CORS headers even to CSRF 403 responses.
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
