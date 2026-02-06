"""Correlation ID utilities for distributed tracing.

Per plan.md: Provides correlation ID propagation to all published events.
Works with the existing RequestIDMiddleware to provide a unified tracing context.

The correlation ID is used to trace requests across services:
- Incoming requests: Use X-Correlation-ID header or X-Request-ID
- Published events: Include correlationid field in CloudEvents
- Logs: Include correlation_id in structured log entries
"""

import logging
from contextvars import ContextVar
from typing import Any

from starlette.requests import Request

logger = logging.getLogger(__name__)

# Context variable for correlation ID (thread-safe)
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in context."""
    _correlation_id.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from context."""
    _correlation_id.set(None)


def get_correlation_id_from_request(request: Request) -> str | None:
    """Extract correlation ID from request.

    Priority:
    1. X-Correlation-ID header (explicit distributed trace)
    2. X-Request-ID header (request tracking)
    3. request.state.request_id (set by RequestIDMiddleware)
    """
    # Check headers first
    correlation_id = request.headers.get("x-correlation-id")
    if correlation_id:
        return correlation_id

    # Fall back to request ID
    request_id = request.headers.get("x-request-id")
    if request_id:
        return request_id

    # Check request state (set by RequestIDMiddleware)
    if hasattr(request.state, "request_id"):
        return request.state.request_id

    return None


class CorrelationIDMiddleware:
    """ASGI middleware for correlation ID management.

    Works alongside RequestIDMiddleware to provide distributed tracing.
    Sets the correlation ID in context for use by services and event publishers.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract correlation ID from headers
        headers = dict(scope.get("headers", []))
        correlation_id = (
            headers.get(b"x-correlation-id", b"").decode()
            or headers.get(b"x-request-id", b"").decode()
            or None
        )

        # Set in context for use during request handling
        if correlation_id:
            set_correlation_id(correlation_id)

        # Add correlation ID to response headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                current_correlation_id = get_correlation_id()
                if current_correlation_id:
                    headers.append(
                        (b"x-correlation-id", current_correlation_id.encode())
                    )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            clear_correlation_id()


def with_correlation_id(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Get log extra dict with correlation ID included.

    Usage:
        logger.info("message", extra=with_correlation_id({"key": "value"}))
    """
    result = extra.copy() if extra else {}
    correlation_id = get_correlation_id()
    if correlation_id:
        result["correlation_id"] = correlation_id
    return result
