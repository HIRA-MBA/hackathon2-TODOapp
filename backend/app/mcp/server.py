"""FastMCP server for ChatKit integration.

Exposes task operations as MCP tools, reusing TaskService for all CRUD.
Supports multiple authentication modes:
1. JWT Bearer token via Authorization header
2. API Key + X-User-ID header for workflow authentication
3. Session token parameter for ChatKit tool calls
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
# Default to None - authentication is REQUIRED for task operations
current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)

mcp = FastMCP(
    name="TodoMCP",
    instructions="""Help users manage their todo list. Use tools to add, list, update, complete, and delete tasks.
Tasks can have priority (high/medium/low) and due dates.

IMPORTANT: All tools require a session_token parameter for authentication.
Always include the session_token when calling any tool.""",
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
    """Pure ASGI middleware to extract user_id from auth header.

    Does NOT block requests - just extracts user context for tools.
    Auth validation happens at tool execution time - tools MUST check auth.

    Supports two authentication modes:
    1. JWT Bearer token - extracts user_id from token's 'sub' claim
    2. API Key + X-User-ID header - for ChatKit workflow authentication
       When a valid API key is present, trusts X-User-ID header for user context
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        user_id_header = headers.get(b"x-user-id", b"").decode()

        # SECURITY: No fallback user - must authenticate
        user_id = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if verify_api_key(token):
                # API key auth - trust X-User-ID header for user context
                # This enables ChatKit workflows to act on behalf of users
                if user_id_header:
                    user_id = user_id_header
                    logger.info(f"MCP auth: API key + X-User-ID header for user {user_id}")
                else:
                    logger.info("MCP auth: Valid API key but no X-User-ID header")
            else:
                # Try JWT authentication
                extracted_id = verify_jwt(token)
                if extracted_id:
                    user_id = extracted_id
                    logger.info(f"MCP auth: JWT user {user_id}")
                else:
                    logger.warning("MCP auth: Invalid token, no user context")

        # Set context and proceed - tools will check for valid user_id
        ctx_token = current_user_id.set(user_id)
        try:
            await self.app(scope, receive, send)
        finally:
            current_user_id.reset(ctx_token)


def get_user_id_from_context() -> str | None:
    """Get current authenticated user_id from context (may be None)."""
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


async def validate_session_token(token: str) -> str | None:
    """Validate a ChatKit session token and return the user_id.

    Args:
        token: The session token to validate

    Returns:
        The user_id if token is valid, None otherwise
    """
    async with get_session() as session:
        stmt = select(ChatkitSession).where(
            ChatkitSession.token == token,
            ChatkitSession.revoked == False,
            ChatkitSession.expires_at > datetime.utcnow(),
        )
        result = await session.execute(stmt)
        session_record = result.scalar_one_or_none()

        if session_record:
            logger.info(f"MCP auth: Valid session token for user {session_record.user_id}")
            return session_record.user_id

        logger.warning("MCP auth: Invalid or expired session token")
        return None


async def get_authenticated_user_id(session_token: str | None = None) -> str | None:
    """Get authenticated user_id from session token or context.

    Priority:
    1. Session token (if provided and valid)
    2. Context (from middleware - JWT or API key auth)

    Args:
        session_token: Optional ChatKit session token

    Returns:
        The user_id if authenticated, None otherwise
    """
    # First try session token if provided
    if session_token:
        user_id = await validate_session_token(session_token)
        if user_id:
            return user_id

    # Fall back to context (from middleware)
    return get_user_id_from_context()


# ============================================================================
# Tool implementations with session_token support
# ============================================================================

@mcp.tool
async def add_task(
    title: str,
    session_token: str | None = None,
    description: str | None = None,
    priority: str = "medium",
    due_date: str | None = None,
) -> str:
    """Add a new task.

    Args:
        title: Task title (required, max 200 characters)
        session_token: Authentication token (required for ChatKit)
        description: Optional task description
        priority: Task priority - "high", "medium" (default), or "low"
        due_date: Optional due date in ISO format (e.g., "2026-01-20")
    """
    user_id = await get_authenticated_user_id(session_token)
    if not user_id:
        return "add_task: error - authentication required. Please provide a valid session_token."

    # Validate inputs
    if not title or not title.strip():
        return "add_task: error - title cannot be empty"

    if len(title) > 200:
        return "add_task: error - title must be 200 characters or less"

    if priority not in ("high", "medium", "low"):
        return f"add_task: error - priority must be 'high', 'medium', or 'low', got '{priority}'"

    # Parse due_date if provided
    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except ValueError:
            return f"add_task: error - invalid due_date format: {due_date}. Use ISO format (e.g., 2026-01-20)"

    async with get_session() as session:
        service = TaskService(session)
        data = TaskCreate(
            title=title.strip(),
            description=description,
            priority=priority,
            due_date=parsed_due_date,
        )
        task = await service.create_task(user_id, data)

        result = f"add_task: success - created task #{task.id} '{task.title}'"
        if task.priority != "medium":
            result += f" (priority: {task.priority})"
        if task.due_date:
            result += f" (due: {task.due_date.strftime('%Y-%m-%d')})"
        return result


@mcp.tool
async def list_tasks(
    session_token: str | None = None,
    status: str = "all",
    search: str | None = None,
    sort_by: str = "created_at",
) -> str:
    """List all tasks with optional filtering.

    Args:
        session_token: Authentication token (required for ChatKit)
        status: Filter by "all", "pending", or "completed"
        search: Optional search term for title matching
        sort_by: Sort order - "created_at" (newest first) or "due_date" (soonest first)
    """
    user_id = await get_authenticated_user_id(session_token)
    if not user_id:
        return "list_tasks: error - authentication required. Please provide a valid session_token."

    async with get_session() as session:
        service = TaskService(session)
        tasks = await service.list_tasks(user_id, sort_by=sort_by)

        # Filter by status
        if status == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif status == "completed":
            tasks = [t for t in tasks if t.completed]

        # Filter by search term
        if search:
            search_lower = search.lower()
            tasks = [t for t in tasks if search_lower in t.title.lower()]

        if not tasks:
            if status == "pending":
                return "list_tasks: No pending tasks found."
            elif status == "completed":
                return "list_tasks: No completed tasks found."
            elif search:
                return f"list_tasks: No tasks matching '{search}' found."
            else:
                return "list_tasks: No tasks found. You can add one by asking me!"

        # Format task list with priority and due date indicators
        lines = [f"list_tasks: Found {len(tasks)} task(s):"]
        today = datetime.now().date()
        for t in tasks:
            status_icon = "[DONE]" if t.completed else "[    ]"
            priority_icon = {"high": "!", "medium": "-", "low": "."}.get(t.priority, "-")

            # Format due date with status indicators
            due_str = ""
            if t.due_date:
                task_due_date = t.due_date.date()
                if task_due_date < today and not t.completed:
                    due_str = f" [OVERDUE: {task_due_date}]"
                elif task_due_date == today:
                    due_str = " [TODAY]"
                else:
                    due_str = f" [due: {task_due_date}]"

            lines.append(f"  [{priority_icon}] #{t.id} {status_icon} {t.title}{due_str}")

        return "\n".join(lines)


@mcp.tool
async def complete_task(
    task_id: str,
    session_token: str | None = None,
) -> str:
    """Mark a task as completed.

    Args:
        task_id: The task UUID to complete
        session_token: Authentication token (required for ChatKit)
    """
    user_id = await get_authenticated_user_id(session_token)
    if not user_id:
        return "complete_task: error - authentication required. Please provide a valid session_token."

    # Validate task_id format
    try:
        uuid = UUID(task_id)
    except ValueError:
        return f"complete_task: error - invalid task ID format: {task_id}"

    async with get_session() as session:
        service = TaskService(session)

        # First check if task exists
        task = await service.get_task(uuid, user_id)
        if not task:
            return f"complete_task: error - task #{task_id} not found"

        if task.completed:
            return f"complete_task: info - task '{task.title}' is already completed"

        # Toggle to complete
        updated_task = await service.toggle_task(uuid, user_id)
        if not updated_task:
            return f"complete_task: error - failed to complete task #{task_id}"

        return f"complete_task: success - marked '{updated_task.title}' as done"


@mcp.tool
async def delete_task(
    task_id: str,
    session_token: str | None = None,
) -> str:
    """Delete a task.

    Args:
        task_id: The task UUID to delete
        session_token: Authentication token (required for ChatKit)
    """
    user_id = await get_authenticated_user_id(session_token)
    if not user_id:
        return "delete_task: error - authentication required. Please provide a valid session_token."

    # Validate task_id format
    try:
        uuid = UUID(task_id)
    except ValueError:
        return f"delete_task: error - invalid task ID format: {task_id}"

    async with get_session() as session:
        service = TaskService(session)

        # Get task title before deletion for confirmation message
        task = await service.get_task(uuid, user_id)
        if not task:
            return f"delete_task: error - task #{task_id} not found"

        task_title = task.title
        deleted = await service.delete_task(uuid, user_id)

        if not deleted:
            return f"delete_task: error - failed to delete task #{task_id}"

        return f"delete_task: success - deleted task '{task_title}'"


@mcp.tool
async def update_task(
    task_id: str,
    session_token: str | None = None,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
) -> str:
    """Update an existing task.

    Args:
        task_id: The task UUID to update (required)
        session_token: Authentication token (required for ChatKit)
        title: New title (optional, max 200 characters)
        description: New description (optional)
        priority: New priority - "high", "medium", or "low" (optional)
        due_date: New due date in ISO format (optional, e.g., "2026-01-20")
    """
    user_id = await get_authenticated_user_id(session_token)
    if not user_id:
        return "update_task: error - authentication required. Please provide a valid session_token."

    # Validate task_id format
    try:
        uuid = UUID(task_id)
    except ValueError:
        return f"update_task: error - invalid task ID format: {task_id}"

    # Validate that at least one field is provided
    if title is None and description is None and priority is None and due_date is None:
        return "update_task: error - must provide at least one field to update"

    # Validate title length if provided
    if title is not None and len(title) > 200:
        return "update_task: error - title must be 200 characters or less"

    # Validate priority if provided
    if priority is not None and priority not in ("high", "medium", "low"):
        return f"update_task: error - priority must be 'high', 'medium', or 'low', got '{priority}'"

    # Parse due_date if provided
    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        except ValueError:
            return f"update_task: error - invalid due_date format: {due_date}. Use ISO format (e.g., 2026-01-20)"

    async with get_session() as session:
        service = TaskService(session)

        # Check if task exists
        existing_task = await service.get_task(uuid, user_id)
        if not existing_task:
            return f"update_task: error - task #{task_id} not found"

        # Build update data
        update_data = TaskUpdate(
            title=title,
            description=description,
            priority=priority,
            due_date=parsed_due_date,
        )

        task = await service.update_task(uuid, user_id, update_data)
        if not task:
            return f"update_task: error - failed to update task #{task_id}"

        return f"update_task: success - updated task #{task.id} '{task.title}'"


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
