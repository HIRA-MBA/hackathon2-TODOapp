"""FastMCP server for ChatKit integration.

Exposes task operations as MCP tools, reusing TaskService for all CRUD.
Authentication is handled via:
1. JWT Bearer token via Authorization header (direct API calls)
2. API Key + X-User-ID header (ChatKit workflow calls)
"""

import logging
from contextvars import ContextVar
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

import jwt
from fastmcp import FastMCP
from sqlalchemy import select

from app.config.database import async_session_maker
from app.config.settings import get_settings
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate
from app.models.chatkit_session import ChatkitSession

logger = logging.getLogger(__name__)
settings = get_settings()

# Context variable to store authenticated user_id for current request
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)

mcp = FastMCP(
    name="TodoMCP",
    instructions="""Help users manage their todo list. Use tools to add, list, update, complete, and delete tasks.
Tasks can have priority (high/medium/low) and due dates.""",
)


def verify_api_key(token: str) -> bool:
    """Verify if token matches the MCP API key."""
    if not settings.mcp_api_key:
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
    """ASGI middleware to extract user_id from auth header or query param.

    Supports:
    1. JWT Bearer token - extracts user_id from token's 'sub' claim
    2. API Key + X-User-ID header - for ChatKit workflow authentication
    3. API Key + user_id query parameter - alternative for workflows that can't set headers
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        user_id_header = headers.get(b"x-user-id", b"").decode()

        # Also check query string for user_id
        query_string = scope.get("query_string", b"").decode()
        user_id_param = ""
        if query_string:
            from urllib.parse import parse_qs
            params = parse_qs(query_string)
            user_id_param = params.get("user_id", [""])[0]

        user_id = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if verify_api_key(token):
                # API key auth - trust X-User-ID header or query param
                if user_id_header:
                    user_id = user_id_header
                    logger.info(f"MCP auth: API key + X-User-ID header for user {user_id}")
                elif user_id_param:
                    user_id = user_id_param
                    logger.info(f"MCP auth: API key + user_id param for user {user_id}")
            else:
                # Try JWT authentication
                extracted_id = verify_jwt(token)
                if extracted_id:
                    user_id = extracted_id
                    logger.info(f"MCP auth: JWT user {user_id}")

        ctx_token = current_user_id.set(user_id)
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(ctx_token)


def get_user_id() -> str:
    """Get current authenticated user_id from context.

    Raises:
        ValueError: If no authenticated user context is available.
    """
    user_id = current_user_id.get()
    if not user_id:
        raise ValueError("Authentication required")
    return user_id


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


async def get_active_session_for_user(user_id: str) -> bool:
    """Check if user has an active ChatKit session."""
    async with get_session() as session:
        stmt = select(ChatkitSession).where(
            ChatkitSession.user_id == user_id,
            ChatkitSession.revoked == False,
            ChatkitSession.expires_at > datetime.utcnow(),
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None


# ============================================================================
# MCP Tools - Simple signatures for OpenAI integration
# ============================================================================

@mcp.tool
async def add_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = "",
) -> str:
    """Add a new task to the todo list.

    Args:
        title: Task title (required)
        description: Task description
        priority: Priority level - high, medium, or low
        due_date: Due date in YYYY-MM-DD format
    """
    try:
        user_id = get_user_id()
    except ValueError:
        return "Error: Not authenticated. Please log in to manage tasks."

    if not title or not title.strip():
        return "Error: Task title cannot be empty."

    if len(title) > 200:
        return "Error: Task title must be 200 characters or less."

    if priority not in ("high", "medium", "low"):
        priority = "medium"

    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except ValueError:
            return f"Error: Invalid date format '{due_date}'. Use YYYY-MM-DD format."

    async with get_session() as session:
        service = TaskService(session)
        data = TaskCreate(
            title=title.strip(),
            description=description if description else None,
            priority=priority,
            due_date=parsed_due_date,
        )
        task = await service.create_task(user_id, data)

        result = f"Created task: {task.title}"
        if task.priority != "medium":
            result += f" (priority: {task.priority})"
        if task.due_date:
            result += f" (due: {task.due_date.strftime('%Y-%m-%d')})"
        return result


@mcp.tool
async def list_tasks(
    filter_status: str = "all",
    search: str = "",
) -> str:
    """List all tasks, optionally filtered.

    Args:
        filter_status: Filter by status - all, pending, or completed
        search: Search term to filter tasks by title
    """
    try:
        user_id = get_user_id()
    except ValueError:
        return "Error: Not authenticated. Please log in to view tasks."

    async with get_session() as session:
        service = TaskService(session)
        tasks = await service.list_tasks(user_id)

        if filter_status == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif filter_status == "completed":
            tasks = [t for t in tasks if t.completed]

        if search:
            search_lower = search.lower()
            tasks = [t for t in tasks if search_lower in t.title.lower()]

        if not tasks:
            if filter_status == "pending":
                return "No pending tasks found."
            elif filter_status == "completed":
                return "No completed tasks found."
            elif search:
                return f"No tasks matching '{search}' found."
            return "No tasks found. Would you like to add one?"

        lines = [f"Found {len(tasks)} task(s):"]
        today = datetime.now().date()

        for t in tasks:
            status = "DONE" if t.completed else "TODO"
            priority_marker = {"high": "!", "medium": "", "low": "."}.get(t.priority, "")

            due_str = ""
            if t.due_date:
                task_due = t.due_date.date()
                if task_due < today and not t.completed:
                    due_str = f" [OVERDUE]"
                elif task_due == today:
                    due_str = " [TODAY]"
                else:
                    due_str = f" [due: {task_due}]"

            lines.append(f"  {priority_marker}[{status}] {t.title}{due_str} (ID: {t.id})")

        return "\n".join(lines)


@mcp.tool
async def complete_task(task_id: str) -> str:
    """Mark a task as completed.

    Args:
        task_id: The ID of the task to complete
    """
    try:
        user_id = get_user_id()
    except ValueError:
        return "Error: Not authenticated. Please log in to manage tasks."

    try:
        uuid = UUID(task_id)
    except ValueError:
        return f"Error: Invalid task ID format."

    async with get_session() as session:
        service = TaskService(session)
        task = await service.get_task(uuid, user_id)

        if not task:
            return f"Error: Task not found."

        if task.completed:
            return f"Task '{task.title}' is already completed."

        updated = await service.toggle_task(uuid, user_id)
        if updated:
            return f"Completed: {updated.title}"
        return "Error: Could not complete task."


@mcp.tool
async def delete_task(task_id: str) -> str:
    """Delete a task permanently.

    Args:
        task_id: The ID of the task to delete
    """
    try:
        user_id = get_user_id()
    except ValueError:
        return "Error: Not authenticated. Please log in to manage tasks."

    try:
        uuid = UUID(task_id)
    except ValueError:
        return f"Error: Invalid task ID format."

    async with get_session() as session:
        service = TaskService(session)
        task = await service.get_task(uuid, user_id)

        if not task:
            return f"Error: Task not found."

        task_title = task.title
        deleted = await service.delete_task(uuid, user_id)

        if deleted:
            return f"Deleted: {task_title}"
        return "Error: Could not delete task."


@mcp.tool
async def update_task(
    task_id: str,
    title: str = "",
    description: str = "",
    priority: str = "",
    due_date: str = "",
) -> str:
    """Update an existing task.

    Args:
        task_id: The ID of the task to update
        title: New title (leave empty to keep current)
        description: New description (leave empty to keep current)
        priority: New priority - high, medium, or low (leave empty to keep current)
        due_date: New due date in YYYY-MM-DD format (leave empty to keep current)
    """
    try:
        user_id = get_user_id()
    except ValueError:
        return "Error: Not authenticated. Please log in to manage tasks."

    try:
        uuid = UUID(task_id)
    except ValueError:
        return f"Error: Invalid task ID format."

    # Check at least one field to update
    if not any([title, description, priority, due_date]):
        return "Error: Please specify at least one field to update."

    if priority and priority not in ("high", "medium", "low"):
        return f"Error: Priority must be high, medium, or low."

    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except ValueError:
            return f"Error: Invalid date format. Use YYYY-MM-DD."

    async with get_session() as session:
        service = TaskService(session)

        existing = await service.get_task(uuid, user_id)
        if not existing:
            return f"Error: Task not found."

        update_data = TaskUpdate(
            title=title if title else None,
            description=description if description else None,
            priority=priority if priority else None,
            due_date=parsed_due_date,
        )

        task = await service.update_task(uuid, user_id, update_data)
        if task:
            return f"Updated: {task.title}"
        return "Error: Could not update task."


# ============================================================================
# App factory
# ============================================================================

_mcp_http_app = None


def get_mcp_http_app():
    """Get or create the MCP HTTP app (singleton)."""
    global _mcp_http_app
    if _mcp_http_app is None:
        _mcp_http_app = mcp.http_app()
    return _mcp_http_app


def create_mcp_app():
    """Create MCP app with auth middleware."""
    return AuthMiddleware(get_mcp_http_app())
