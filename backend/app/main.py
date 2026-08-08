import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.csrf import CSRFMiddleware
from app.core.rate_limit import limiter
from app.services.ws_manager import ws_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # WebSocket pushes are triggered from sync route handlers running in FastAPI's
    # threadpool; binding the loop here lets ws_manager hop back onto it safely.
    ws_manager.bind_loop(asyncio.get_running_loop())
    yield


app = FastAPI(
    title=settings.app_name,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
