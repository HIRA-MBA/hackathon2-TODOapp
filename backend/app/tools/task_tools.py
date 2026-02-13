"""MCP tools for task management operations.

Per spec FR-014 through FR-018: System MUST expose task operation tools.
Per spec FR-019: All tools MUST operate through the service layer.
Per spec FR-028: Parse due date expressions from natural language.
Per research Decision 4: 5 atomic tools with verb_noun naming.
Per research Decision 5: Tools return errors as strings for agent interpretation.
"""

from datetime import datetime
from uuid import UUID

import dateparser
from agents import function_tool, RunContextWrapper

from app.agent.context import UserContext
from app.services.task_service import TaskService
from app.schemas.task import TaskCreate, TaskUpdate


def parse_due_date(date_string: str) -> datetime | None:
    """Parse a due date from natural language or ISO format.

    Per spec FR-028: System MUST parse due date expressions from natural language
    (e.g., "tomorrow", "next Friday", "in 3 days").

    Args:
        date_string: Date string in natural language or ISO format.

    Returns:
        Parsed datetime or None if parsing failed.
    """
    if not date_string:
        return None

    # First try ISO format for explicit dates
    try:
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Then try natural language parsing
    parsed = dateparser.parse(
        date_string,
        settings={
            "PREFER_DATES_FROM": "future",  # Prefer future dates
            "RELATIVE_BASE": datetime.now(),  # Base for relative dates
        },
    )

    return parsed


@function_tool
async def add_task(
    ctx: RunContextWrapper[UserContext],
    title: str,
    description: str | None = None,
    priority: str = "medium",
    due_date: str | None = None,
) -> str:
    """Add a new task for the user.

    Args:
        title: The task title (required, max 200 characters)
        description: Optional task description
        priority: Task priority - "high", "medium" (default), or "low"
        due_date: Optional due date - supports natural language (e.g., "tomorrow", "next Friday", "in 3 days") or ISO format (e.g., "2026-01-20")

    Returns:
        Success message with task ID or error message.
    """
    try:
        if not title or not title.strip():
            return "add_task: error - title cannot be empty"

        if len(title) > 200:
            return "add_task: error - title must be 200 characters or less"

        if priority not in ("high", "medium", "low"):
            return f"add_task: error - priority must be 'high', 'medium', or 'low', got '{priority}'"

        # Parse due_date if provided (supports natural language per FR-028)
        parsed_due_date = None
        if due_date:
            parsed_due_date = parse_due_date(due_date)
            if not parsed_due_date:
                return f"add_task: error - could not understand due date: '{due_date}'. Try formats like 'tomorrow', 'next Friday', 'in 3 days', or '2026-01-20'"

        service = TaskService(ctx.context.db)
        task_data = TaskCreate(
            title=title.strip(),
            description=description,
            priority=priority,
            due_date=parsed_due_date,
        )
        task = await service.create_task(ctx.context.user_id, task_data)

        result = f"add_task: success - created task #{task.id} '{task.title}'"
        if task.priority != "medium":
            result += f" (priority: {task.priority})"
        if task.due_date:
            result += f" (due: {task.due_date.strftime('%Y-%m-%d')})"
        return result
    except Exception as e:
        return f"add_task: error - {str(e)}"


@function_tool
async def list_tasks(
    ctx: RunContextWrapper[UserContext],
    status: str = "all",
    search: str | None = None,
    sort_by: str = "created_at",
) -> str:
    """List the user's tasks with optional filtering.

    Args:
        status: Filter by status - "all", "pending", or "completed"
        search: Optional search term for title matching
        sort_by: Sort order - "created_at" (newest first) or "due_date" (soonest first)

    Returns:
        Formatted task list or message if no tasks found.
    """
    try:
        service = TaskService(ctx.context.db)
        tasks = await service.list_tasks(ctx.context.user_id, sort_by=sort_by)

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

        # Format task list with priority and due date
        lines = [f"list_tasks: Found {len(tasks)} task(s):"]
        today = datetime.now().date()
        for task in tasks:
            status_icon = "[DONE]" if task.completed else "[    ]"
            priority_icon = {"high": "!", "medium": "-", "low": "."}.get(
                task.priority, "-"
            )

            # Format due date
            due_str = ""
            if task.due_date:
                due_date = task.due_date.date()
                if due_date < today and not task.completed:
                    due_str = f" [OVERDUE: {due_date}]"
                elif due_date == today:
                    due_str = " [TODAY]"
                else:
                    due_str = f" [due: {due_date}]"

            lines.append(
                f"  [{priority_icon}] #{task.id} {status_icon} {task.title}{due_str}"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"list_tasks: error - {str(e)}"


@function_tool
async def update_task(
    ctx: RunContextWrapper[UserContext],
    task_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
) -> str:
    """Update an existing task's title, description, priority, or due date.

    Args:
        task_id: The task UUID to update
        title: New title (optional)
        description: New description (optional)
        priority: New priority - "high", "medium", or "low" (optional)
        due_date: New due date - supports natural language (e.g., "tomorrow", "next Friday") or ISO format (optional)

    Returns:
        Success message or error message.
    """
    try:
        # Validate task_id
        try:
            uuid = UUID(task_id)
        except ValueError:
            return f"update_task: error - invalid task ID format: {task_id}"

        if not title and description is None and priority is None and due_date is None:
            return "update_task: error - must provide at least one field to update"

        if title and len(title) > 200:
            return "update_task: error - title must be 200 characters or less"

        if priority is not None and priority not in ("high", "medium", "low"):
            return f"update_task: error - priority must be 'high', 'medium', or 'low', got '{priority}'"

        # Parse due_date if provided (supports natural language per FR-028)
        parsed_due_date = None
        if due_date:
            parsed_due_date = parse_due_date(due_date)
            if not parsed_due_date:
                return f"update_task: error - could not understand due date: '{due_date}'. Try formats like 'tomorrow', 'next Friday', 'in 3 days', or '2026-01-20'"

        service = TaskService(ctx.context.db)
        task_data = TaskUpdate(
            title=title,
            description=description,
            priority=priority,
            due_date=parsed_due_date,
        )
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
