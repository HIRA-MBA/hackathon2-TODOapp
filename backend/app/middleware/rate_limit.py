"""Rate limiting middleware for chat endpoint.

Per spec FR-026: System MUST enforce rate limiting of 20 requests per minute
per authenticated user, returning a friendly "Please slow down" message when exceeded.
"""

import time
import logging
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# Rate limit configuration per FR-026
RATE_LIMIT_REQUESTS = 20  # requests per window
RATE_LIMIT_WINDOW_SECONDS = 60  # 1 minute window


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces per-user rate limiting on chat endpoints.

    Uses sliding window counter algorithm with in-memory storage.
    Rate limit: 20 requests per minute per authenticated user.

    Per spec FR-026: Returns friendly "Please slow down" message when exceeded.
    """

    def __init__(self, app, paths: list[str] | None = None):
        """Initialize rate limiter.

        Args:
            app: The ASGI application
            paths: List of path prefixes to rate limit (default: ["/api/chat"])
        """
        super().__init__(app)
        self.paths = paths or ["/api/chat"]
        # Store request timestamps per user: {user_id: [timestamp1, timestamp2, ...]}
        self._request_times: dict[str, list[float]] = defaultdict(list)

    def _get_user_id_from_request(self, request: Request) -> str | None:
        """Extract user ID from request state (set by auth dependency).

        Falls back to checking Authorization header for JWT parsing.
        """
        # Try to get from request state (set by previous middleware/deps)
        if hasattr(request.state, "user_id"):
            return request.state.user_id

        # Try to extract from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # For rate limiting, we use the token itself as identifier
            # This is acceptable since we just need a unique per-user key
            token = auth_header[7:]
            # Use first 32 chars of token as user identifier (enough for uniqueness)
            return f"token:{token[:32]}" if token else None

        return None

    def _is_rate_limited_path(self, path: str) -> bool:
        """Check if the request path should be rate limited."""
        return any(path.startswith(p) for p in self.paths)

    def _cleanup_old_requests(self, user_id: str, current_time: float) -> None:
        """Remove request timestamps older than the rate limit window."""
        cutoff = current_time - RATE_LIMIT_WINDOW_SECONDS
        self._request_times[user_id] = [
            t for t in self._request_times[user_id] if t > cutoff
        ]

    def _is_rate_limited(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        current_time = time.time()

        # Clean up old requests
        self._cleanup_old_requests(user_id, current_time)

        # Check if over limit
        request_count = len(self._request_times[user_id])
        if request_count >= RATE_LIMIT_REQUESTS:
            return True

        # Record this request
        self._request_times[user_id].append(current_time)
        return False

    def _get_retry_after(self, user_id: str) -> int:
        """Calculate seconds until rate limit resets."""
        if not self._request_times[user_id]:
            return 0

        oldest_request = min(self._request_times[user_id])
        retry_after = int(oldest_request + RATE_LIMIT_WINDOW_SECONDS - time.time())
        return max(1, retry_after)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting check."""
        # Only apply rate limiting to specific paths
        if not self._is_rate_limited_path(request.url.path):
            return await call_next(request)

        # Only rate limit POST requests (the actual chat messages)
        if request.method != "POST":
            return await call_next(request)

        # Get user identifier
        user_id = self._get_user_id_from_request(request)
        if not user_id:
            # No user ID means unauthenticated - let auth middleware handle it
            return await call_next(request)

        # Check rate limit
        if self._is_rate_limited(user_id):
            retry_after = self._get_retry_after(user_id)

            # Log rate limit hit
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "user_id": user_id,
                    "path": request.url.path,
                    "retry_after": retry_after,
                    "request_id": getattr(request.state, "request_id", None),
                }
            )

            # Return friendly message per FR-026
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Please slow down. You've sent too many messages. Try again in a moment.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
