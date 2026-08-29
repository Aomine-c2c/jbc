import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import uuid

from app.db.session import async_session_factory
from app.modules.common.models import AuditLog
from app.core.config import settings

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # We process the request first
        response = await call_next(request)
        
        # Only log API requests
        if not request.url.path.startswith("/api/"):
            return response
            
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.get_secret_key, algorithms=[settings.ALGORITHM])
                sub = payload.get("sub")
                if sub:
                    user_id = uuid.UUID(sub)
            except (JWTError, ValueError):
                pass
                
        # Log to DB asynchronously in the background? 
        # Middleware is async, we can do it here, but it adds latency.
        # For simplicity, we just await it.
        body_str = _safe_audit_body(request)
            
        # create new session since we are out of router context
        async with async_session_factory() as session:
            audit = AuditLog(
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_body=body_str
            )
            session.add(audit)
            try:
                await session.commit()
            except Exception as e:
                print(f"Failed to save audit log: {e}")
                
        return response


SENSITIVE_AUDIT_FIELDS = {
    "password", "hashed_password", "token", "access_token", "refresh_token",
    "authorization", "secret", "secret_key", "signature",
}


def _redact(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_AUDIT_FIELDS else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _safe_audit_body(request: Request) -> str | None:
    """Keep useful structured audit context without persisting secrets or files."""
    content_type = request.headers.get("content-type", "").lower()
    if not content_type.startswith("application/json"):
        return "[omitted: non-JSON request body]" if content_type else None
    try:
        body = request._body if hasattr(request, "_body") else b""
        if not body:
            return None
        redacted = _redact(json.loads(body))
        return json.dumps(redacted, separators=(",", ":"))[:4000]
    except (TypeError, ValueError, UnicodeDecodeError):
        return "[omitted: unreadable JSON request body]"
