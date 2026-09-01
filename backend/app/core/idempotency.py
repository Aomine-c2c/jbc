import time
import json
from typing import Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.logging_config import logger


class IdempotencyStore:
    """
    In-memory TTL Idempotency Cache.
    Prevents duplicate creation of Job Cards, Approvals, and Requisitions
    when network retries or duplicate client submissions occur.
    """

    def __init__(self, ttl_seconds: int = 900):  # 15 minutes TTL
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _cleanup(self):
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v["timestamp"] > self.ttl_seconds]
        for k in expired:
            del self._cache[k]

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        self._cleanup()
        return self._cache.get(key)

    def set(self, key: str, status_code: int, content: bytes, headers: dict):
        self._cleanup()
        self._cache[key] = {
            "status_code": status_code,
            "content": content,
            "headers": dict(headers),
            "timestamp": time.time(),
        }


# Global store instance
idempotency_store = IdempotencyStore()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette middleware that intercepts mutating requests
    bearing an 'X-Idempotency-Key' header.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # Build compound cache key with path and method
        cache_key = f"{request.method}:{request.url.path}:{idempotency_key}"

        cached = idempotency_store.get(cache_key)
        if cached:
            logger.info(f"Idempotent request replay detected for key '{idempotency_key}' on {request.url.path}")
            response = Response(
                content=cached["content"],
                status_code=cached["status_code"],
                media_type=cached["headers"].get("content-type", "application/json"),
            )
            response.headers["X-Idempotency-Replay"] = "true"
            response.headers["X-Idempotency-Key"] = idempotency_key
            return response

        # Process new request
        response = await call_next(request)

        # Cache only successful responses (2xx / 3xx).
        # Never cache client errors (4xx) or transient server errors (5xx),
        # because 4xx payloads are often stale on retry after the user fixes input.
        if response.status_code < 300:
            response_body = [section async for section in response.body_iterator]
            full_body = b"".join(response_body)

            idempotency_store.set(
                cache_key,
                status_code=response.status_code,
                content=full_body,
                headers=dict(response.headers),
            )

            # Reconstruct response for client
            new_response = Response(
                content=full_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
            new_response.headers["X-Idempotency-Key"] = idempotency_key
            return new_response

        return response
