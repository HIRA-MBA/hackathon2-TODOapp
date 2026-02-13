"""Request ID middleware for distributed tracing.

Per spec FR-024: System MUST generate structured logs with unique request IDs.
Per Task 6.3: Unique request_id generated for each chat request (UUID).
"""

import uuid
import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that adds unique request ID to each request.

    Features:
    - Generates UUID for each incoming request
    - Attaches request_id to request.state for use in handlers
    - Adds X-Request-ID header to response
    - Logs request start/end with timing metrics

    Per spec FR-024: Structured logs with unique request IDs.
    Per spec FR-025: Capture key metrics including request latency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with ID tracking and timing."""
        # Use incoming X-Request-ID if present, otherwise generate new one
        # Per AC-030: Support distributed tracing across frontend and backend
        incoming_request_id = request.headers.get("x-request-id")
        request_id = incoming_request_id if incoming_request_id else str(uuid.uuid4())

        # Attach to request state for use in handlers
        request.state.request_id = request_id

        # Record start time for latency calculation
        start_time = time.perf_counter()

        # Log request start
        logger.info(
            "request_started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else "unknown",
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency_ms, 2),
                },
            )

            return response

        except Exception as e:
            # Calculate latency even for errors
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Log error
            logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "latency_ms": round(latency_ms, 2),
                },
                exc_info=True,
            )
            raise
