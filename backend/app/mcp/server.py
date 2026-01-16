"""FastMCP server for ChatKit integration.

Exposes task operations as MCP tools, reusing TaskService for all CRUD.
Supports JWT authentication via Authorization header.
"""

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from uuid import UUID

import jwt
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount

from app.config.database import async_session_maker
from app.config.settings import get_settings
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate

logger = logging.getLogger(__name__)
settings = get_settings()

# Context variable to store authenticated user_id for current request
current_user_id: ContextVar[str] = ContextVar("current_user_id", default="anonymous")

mcp = FastMCP(
    name="TodoMCP",
    instructions="Help users manage their todo list. Use tools to add, list, complete, and delete tasks.",
)


def verify_api_key(token: str) -> bool:
    """Verify if token matches the MCP API key."""
    if not settings.mcp_api_key:
        # No API key configured, allow all requests
        return True
    return token == settings.mcp_api_key


def verify_jwt(token: str) -> str | None:
    """Verify JWT and return user_id (sub claim) or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            settings.better_auth_secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        logger.warning("MCP auth: Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"MCP auth: Invalid token - {e}")
        return None


class AuthMiddleware:
    """Pure ASGI middleware to verify API key and extract user_id.

    Allows MCP discovery (initialize, tools/list) without auth.
    Requires auth only for tool execution (tools/call).
    """

    # MCP methods that don't require authentication
    PUBLIC_METHODS = {"initialize", "tools/list", "ping"}

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        # Check if this is a public MCP method (read body for JSON-RPC)
        is_public = await self._is_public_method(scope, receive)

        user_id = "chatkit-user"

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

            if verify_api_key(token):
                logger.info("MCP auth: Valid API key")
            else:
                extracted_id = verify_jwt(token)
                if extracted_id:
                    user_id = extracted_id
                    logger.info(f"MCP auth: JWT user {user_id}")
                elif settings.mcp_api_key and not is_public:
                    response = JSONResponse(
                        status_code=401,
                        content={"error": "Invalid authentication token"}
                    )
                    await response(scope, receive, send)
                    return
        elif settings.mcp_api_key and not is_public:
            response = JSONResponse(
                status_code=401,
                content={"error": "Authentication required"}
            )
            await response(scope, receive, send)
            return

        # Set context and proceed (use wrapped receive if body was read)
        ctx_token = current_user_id.set(user_id)
        try:
            actual_receive = scope.get("_wrapped_receive", receive)
            await self.app(scope, actual_receive, send)
        finally:
            current_user_id.reset(ctx_token)

    async def _is_public_method(self, scope, receive) -> bool:
        """Check if request is a public MCP method by inspecting JSON-RPC body."""
        import json

        # GET/HEAD/OPTIONS are public (SSE, health, CORS preflight)
        method = scope.get("method", "GET")
        if method in ("GET", "HEAD", "OPTIONS"):
            return True

        # For POST, check JSON-RPC method
        if method == "POST":
            body, wrapped_receive = await self._read_and_wrap_body(receive)
            scope["_wrapped_receive"] = wrapped_receive
            try:
                data = json.loads(body) if body else {}
                rpc_method = data.get("method", "")
                return rpc_method in self.PUBLIC_METHODS
            except (json.JSONDecodeError, AttributeError):
                return False
        return False

    async def _read_and_wrap_body(self, receive):
        """Read body and return wrapped receive that replays it."""
        body_parts = []
        while True:
            message = await receive()
            body = message.get("body", b"")
            if body:
                body_parts.append(body)
            if not message.get("more_body", False):
                break

        full_body = b"".join(body_parts)

        # Create receive wrapper that replays the body
        body_sent = False
        async def wrapped_receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": full_body, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        return full_body, wrapped_receive


def get_user_id() -> str:
    """Get current authenticated user_id from context."""
    return current_user_id.get()


@asynccontextmanager
async def get_session():
    """Get async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@mcp.tool
async def add_task(title: str, description: str | None = None) -> str:
    """Add a new task.

    Args:
        title: Task title (required)
        description: Optional description
    """
    user_id = get_user_id()
    async with get_session() as session:
        service = TaskService(session)
        data = TaskCreate(title=title.strip(), description=description)
        task = await service.create_task(user_id, data)
        return f"Created task: {task.title} (ID: {task.id})"


@mcp.tool
async def list_tasks(status: str = "all") -> str:
    """List all tasks.

    Args:
        status: Filter by "all", "pending", or "completed"
    """
    user_id = get_user_id()
    async with get_session() as session:
        service = TaskService(session)
        tasks = await service.list_tasks(user_id)

        if status == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif status == "completed":
            tasks = [t for t in tasks if t.completed]

        if not tasks:
            return "No tasks found."

        lines = [f"Found {len(tasks)} task(s):"]
        for t in tasks:
            icon = "[x]" if t.completed else "[ ]"
            lines.append(f"  {icon} {t.title} (ID: {t.id})")
        return "\n".join(lines)


@mcp.tool
async def complete_task(task_id: str) -> str:
    """Mark a task as completed.

    Args:
        task_id: The task UUID to complete
    """
    user_id = get_user_id()
    async with get_session() as session:
        service = TaskService(session)
        try:
            task = await service.toggle_task(UUID(task_id), user_id)
            if not task:
                return f"Task {task_id} not found."
            status = "completed" if task.completed else "pending"
            return f"Marked '{task.title}' as {status}."
        except ValueError:
            return f"Invalid task ID: {task_id}"


@mcp.tool
async def delete_task(task_id: str) -> str:
    """Delete a task.

    Args:
        task_id: The task UUID to delete
    """
    user_id = get_user_id()
    async with get_session() as session:
        service = TaskService(session)
        try:
            task = await service.get_task(UUID(task_id), user_id)
            if not task:
                return f"Task {task_id} not found."
            title = task.title
            await service.delete_task(UUID(task_id), user_id)
            return f"Deleted task: {title}"
        except ValueError:
            return f"Invalid task ID: {task_id}"


# Create the http_app once so we can share its lifespan
_mcp_http_app = None


def get_mcp_http_app():
    """Get or create the MCP HTTP app (singleton)."""
    global _mcp_http_app
    if _mcp_http_app is None:
        _mcp_http_app = mcp.http_app()
    return _mcp_http_app


def create_mcp_app():
    """Create MCP app with auth middleware."""
    # Use the singleton http_app
    return AuthMiddleware(get_mcp_http_app())
