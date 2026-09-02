from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """Require a same-session CSRF token for cookie-authenticated mutations."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    EXEMPT_PATHS = {"/api/v1/iam/auth/login", "/api/v1/iam/auth/refresh", "/api/v1/dashboard/metrics"}

    async def dispatch(self, request: Request, call_next):
        # Bearer token authentication is inherently immune to browser CSRF
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return await call_next(request)

        uses_cookie_auth = bool(request.cookies.get("dwrms_access_token"))
        if (
            uses_cookie_auth
            and request.method not in self.SAFE_METHODS
            and request.url.path not in self.EXEMPT_PATHS
        ):
            csrf_header = request.headers.get("X-CSRF-Token")
            csrf_cookie = request.cookies.get("dwrms_csrf_token")
            if not csrf_header or (csrf_cookie and csrf_header != csrf_cookie):
                return JSONResponse(status_code=403, content={"detail": "Invalid CSRF token"})
        return await call_next(request)

