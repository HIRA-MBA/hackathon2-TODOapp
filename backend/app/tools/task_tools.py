"""MCP tools for task management operations.

Per spec FR-014 through FR-018: System MUST expose task operation tools.
Per spec FR-019: All tools MUST operate through the service layer.
Per research Decision 4: 5 atomic tools with verb_noun naming.
Per research Decision 5: Tools return errors as strings for agent interpretation.
"""

from uuid import UUID

from agents import function_tool, RunContextWrapper

from app.agent.context import UserContext
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate


@function_tool
async def add_task(
    ctx: RunContextWrapper[UserContext],
    title: str,
    description: str | None = None,
) -> str:
    """Add a new task for the user.

    Args:
        title: The task title (required, max 200 characters)
        description: Optional task description

    Returns:
        Success message with task ID or error message.
    """
    try:
        if not title or not title.strip():
            return "add_task: error - title cannot be empty"

        if len(title) > 200:
            return "add_task: error - title must be 200 characters or less"

        service = TaskService(ctx.context.db)
        task_data = TaskCreate(title=title.strip(), description=description)
        task = await service.create_task(ctx.context.user_id, task_data)

        return f"add_task: success - created task #{task.id} '{task.title}'"
    except Exception as e:
        return f"add_task: error - {str(e)}"


@function_tool
async def list_tasks(
    ctx: RunContextWrapper[UserContext],
    status: str = "all",
    search: str | None = None,
) -> str:
    """List the user's tasks with optional filtering.

    Args:
        status: Filter by status - "all", "pending", or "completed"
        search: Optional search term for title matching

    Returns:
        Formatted task list or message if no tasks found.
    """
    try:
        service = TaskService(ctx.context.db)
        tasks = await service.list_tasks(ctx.context.user_id)

        # Filter by status
        if status == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif status == "completed":
            tasks = [t for t in tasks if t.completed]
        # "all" returns everything

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

        # Format task list
        lines = [f"list_tasks: Found {len(tasks)} task(s):"]
        for task in tasks:
            status_icon = "[DONE]" if task.completed else "[    ]"
            lines.append(f"  #{task.id} {status_icon} {task.title}")

        return "\n".join(lines)
    except Exception as e:
        return f"list_tasks: error - {str(e)}"


@function_tool
async def update_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str,
    title: str | None = None,
    description: str | None = None,
) -> str:
    """Update an existing task's title or description.

    Args:
        task_id: The task UUID to update
        title: New title (optional)
        description: New description (optional)

    Returns:
        Success message or error message.
    """
    try:
        # Validate task_id
        try:
            uuid = UUID(task_id)
        except ValueError:
            return f"update_task: error - invalid task ID format: {task_id}"

        if not title and description is None:
            return "update_task: error - must provide title or description to update"

        if title and len(title) > 200:
            return "update_task: error - title must be 200 characters or less"

        service = TaskService(ctx.context.db)
        task_data = TaskUpdate(title=title, description=description)
        task = await service.update_task(uuid, ctx.context.user_id, task_data)

        if not task:
            return f"update_task: error - task #{task_id} not found"

        return f"update_task: success - updated task #{task.id} '{task.title}'"
    except Exception as e:
        return f"update_task: error - {str(e)}"


@function_tool
async def complete_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str,
) -> str:
    """Mark a task as completed.

    Args:
        task_id: The task UUID to complete

    Returns:
        Success message or error message.
    """
    try:
        # Validate task_id
        try:
            uuid = UUID(task_id)
        except ValueError:
            return f"complete_task: error - invalid task ID format: {task_id}"

        service = TaskService(ctx.context.db)

        # First check if task exists and get its current status
        task = await service.get_task(uuid, ctx.context.user_id)
        if not task:
            return f"complete_task: error - task #{task_id} not found"

        if task.completed:
            return f"complete_task: info - task '{task.title}' is already completed"

        # Toggle to complete
        updated_task = await service.toggle_task(uuid, ctx.context.user_id)
        if not updated_task:
            return f"complete_task: error - failed to complete task #{task_id}"

        return f"complete_task: success - marked '{updated_task.title}' as done"
    except Exception as e:
        return f"complete_task: error - {str(e)}"


@function_tool
async def delete_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str,
) -> str:
    """Delete a task.

    Args:
        task_id: The task UUID to delete

    Returns:
        Success message or error message.
    """
    try:
        # Validate task_id
        try:
            uuid = UUID(task_id)
        except ValueError:
            return f"delete_task: error - invalid task ID format: {task_id}"

        service = TaskService(ctx.context.db)

        # Get task title before deletion for confirmation message
        task = await service.get_task(uuid, ctx.context.user_id)
        if not task:
            return f"delete_task: error - task #{task_id} not found"

        task_title = task.title
        deleted = await service.delete_task(uuid, ctx.context.user_id)

        if not deleted:
            return f"delete_task: error - failed to delete task #{task_id}"

        return f"delete_task: success - deleted task '{task_title}'"
    except Exception as e:
        return f"delete_task: error - {str(e)}"
