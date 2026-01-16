"""FastMCP server for ChatKit integration.

Exposes task operations as MCP tools, reusing TaskService for all CRUD.
"""

from contextlib import asynccontextmanager
from uuid import UUID
from fastmcp import FastMCP

from app.config.database import async_session_maker
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate

mcp = FastMCP(
    name="TodoMCP",
    instructions="Help users manage their todo list. Use tools to add, list, complete, and delete tasks.",
)


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
    async with get_session() as session:
        service = TaskService(session)
        data = TaskCreate(title=title.strip(), description=description)
        task = await service.create_task("mcp-user", data)
        return f"Created task: {task.title} (ID: {task.id})"


@mcp.tool
async def list_tasks(status: str = "all") -> str:
    """List all tasks.

    Args:
        status: Filter by "all", "pending", or "completed"
    """
    async with get_session() as session:
        service = TaskService(session)
        tasks = await service.list_tasks("mcp-user")

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
    async with get_session() as session:
        service = TaskService(session)
        try:
            task = await service.toggle_task(UUID(task_id), "mcp-user")
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
    async with get_session() as session:
        service = TaskService(session)
        try:
            task = await service.get_task(UUID(task_id), "mcp-user")
            if not task:
                return f"Task {task_id} not found."
            title = task.title
            await service.delete_task(UUID(task_id), "mcp-user")
            return f"Deleted task: {title}"
        except ValueError:
            return f"Invalid task ID: {task_id}"
