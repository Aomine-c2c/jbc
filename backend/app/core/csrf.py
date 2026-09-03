from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """Require a same-session CSRF token for cookie-authenticated mutations."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    EXEMPT_PATHS = {"/api/v1/iam/auth/login", "/api/v1/iam/auth/refresh", "/api/v1/dashboard/metrics"}
    EXEMPT_PREFIXES = ("/api/v1/setup",)

    async def dispatch(self, request: Request, call_next):
        # Bearer token authentication is inherently immune to browser CSRF
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return await call_next(request)

        uses_cookie_auth = bool(request.cookies.get("dwrms_access_token"))
        is_exempt = request.url.path in self.EXEMPT_PATHS or any(request.url.path.startswith(p) for p in self.EXEMPT_PREFIXES)
        if (
            uses_cookie_auth
            and request.method not in self.SAFE_METHODS
            and not is_exempt
        ):
            csrf_header = request.headers.get("X-CSRF-Token")
            csrf_cookie = request.cookies.get("dwrms_csrf_token")
            if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
                return JSONResponse(status_code=403, content={"detail": "Invalid CSRF token"})
        return await call_next(request)

