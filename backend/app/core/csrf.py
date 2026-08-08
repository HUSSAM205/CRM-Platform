from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Endpoints reachable before a session (or its CSRF cookie) exists yet. Login/register
# are protected by requiring the correct password instead; accepting an invitation is
# gated by a one-time token in the URL. Refresh is exempt because it runs the token
# reuse-detection check itself, which serves the same purpose CSRF protection would here.
EXEMPT_PATH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/invitations/",
)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection for cookie-authenticated mutating requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        is_exempt = any(path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES)

        if request.method not in SAFE_METHODS and not is_exempt:
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("x-csrf-token")
            if not cookie_token or not header_token or cookie_token != header_token:
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)

        return await call_next(request)
