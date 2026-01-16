"""FastMCP server for ChatKit integration.

Exposes task operations as MCP tools, reusing TaskService for all CRUD.
Supports JWT authentication via Authorization header or user_token parameter.
"""

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from uuid import UUID

import jwt
from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

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


def verify_token(token: str) -> str | None:
    """Verify JWT and return user_id (sub claim) or None if invalid."""
    try:
        # Try HS256 with shared secret (Better Auth default)
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


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to extract user_id from JWT in Authorization header."""

    async def dispatch(self, request: Request, call_next):
        user_id = "anonymous"

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            extracted_id = verify_token(token)
            if extracted_id:
                user_id = extracted_id
                logger.info(f"MCP auth: Authenticated user {user_id}")

        # Set context variable for tools to access
        token = current_user_id.set(user_id)
        try:
            response = await call_next(request)
            return response
        finally:
            current_user_id.reset(token)


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


def create_mcp_app():
    """Create MCP app with auth middleware."""
    app = mcp.http_app()
    app.add_middleware(AuthMiddleware)
    return app
