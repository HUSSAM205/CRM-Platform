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
    """Double-submit cookie CSRF protection for cookie-authenticated mutating requests.

    The csrf_token cookie is deliberately not httpOnly so frontend JS can read it via
    document.cookie and echo it back as a header - that's what makes this a *double*
    submit (attacker can trigger the cookie to be sent, but can't read its value to
    forge the header). That read-via-document.cookie trick only works same-site,
    though: in production the frontend (e.g. *.vercel.app) and backend (e.g.
    *.onrender.com) are different domains, so a cookie set by the backend is invisible
    to frontend JS entirely. To keep this working cross-origin, every response here
    also echoes the current cookie value back as an X-CSRF-Token *response* header
    (exposed via CORS's expose_headers) - the frontend reads it from there instead of
    from document.cookie, which works identically same-site or cross-site.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        is_exempt = any(path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES)

        if request.method not in SAFE_METHODS and not is_exempt:
            cookie_token = request.cookies.get("csrf_token")
            header_token = request.headers.get("x-csrf-token")
            if not cookie_token or not header_token or cookie_token != header_token:
                return JSONResponse({"detail": "CSRF token missing or invalid"}, status_code=403)

        response = await call_next(request)

        # Prefer a token this response just *set* (login/register/refresh issue a new
        # one) over the incoming request's existing cookie, since the new value is what
        # the browser will actually hold from now on.
        newly_set_token = None
        for key, value in response.raw_headers:
            if key == b"set-cookie" and value.startswith(b"csrf_token="):
                newly_set_token = value.split(b";", 1)[0].split(b"=", 1)[1].decode()
                break

        token_to_echo = newly_set_token or request.cookies.get("csrf_token")
        if token_to_echo:
            response.headers["X-CSRF-Token"] = token_to_echo

        return response
