from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """Require a same-session CSRF token for cookie-authenticated mutations."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
    EXEMPT_PATHS = {"/api/v1/iam/auth/login"}

    async def dispatch(self, request: Request, call_next):
        uses_cookie_auth = bool(request.cookies.get("dwrms_access_token"))
        if (
            uses_cookie_auth
            and request.method not in self.SAFE_METHODS
            and request.url.path not in self.EXEMPT_PATHS
            and request.headers.get("X-CSRF-Token") != request.cookies.get("dwrms_csrf_token")
        ):
            return JSONResponse(status_code=403, content={"detail": "Invalid CSRF token"})
        return await call_next(request)
