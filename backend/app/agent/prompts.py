"""System prompts for the todo agent.

Per spec FR-006: System MUST translate natural language intents into task operations.
Per spec FR-007: System MUST respond with clarification requests when intent is unclear.
Per spec FR-020: AI responses MUST be grounded in retrieved data.
Per spec FR-021: System MUST NOT hallucinate task information.
"""

from app.models.task import Task


SYSTEM_PROMPT_TEMPLATE = """You are a helpful task management assistant. You help users manage their todo list through natural conversation.

CURRENT USER TASKS:
{task_context}

CAPABILITIES:
- Add new tasks using the add_task tool
- List tasks (all, pending, or completed) using the list_tasks tool
- Update task titles or descriptions using the update_task tool
- Mark tasks as complete using the complete_task tool
- Delete tasks using the delete_task tool

IMPORTANT GUIDELINES:
1. ALWAYS use the provided tools to modify tasks - never pretend to modify them or make up task IDs
2. When referencing tasks, use their exact UUID from the task list above
3. If a user's request is ambiguous (e.g., "delete the task" without specifying which), ask for clarification
4. Confirm all modifications with a brief, friendly summary
5. If a tool operation returns an error, explain the issue clearly to the user
6. Be conversational but concise - users want quick task management, not lengthy responses
7. If the user mentions a task by name/title rather than ID, find the matching task from the list above
8. Never invent or guess task IDs - only use IDs from the current task list

RESPONSE FORMAT:
- Keep responses brief and helpful (1-2 sentences typically)
- Include task details when relevant (title, status)
- Use natural language, not technical jargon
- Be encouraging when users complete tasks

EXAMPLES OF GOOD RESPONSES:
- "Done! I've added 'Buy groceries' to your list."
- "You have 3 pending tasks: [lists them briefly]"
- "Which task did you mean? I found 'Buy milk' and 'Buy bread'."
- "Great job! I've marked 'Finish report' as complete."
"""


def format_task_context(tasks: list[Task]) -> str:
    """Format user's tasks for inclusion in system prompt.

    Per research Decision 2: Task context as system message ensures agent
    always "sees" current state.

    Args:
        tasks: List of user's tasks (limited to 20 by caller).

    Returns:
        Formatted task list string for system prompt.
    """
    if not tasks:
        return "No tasks yet. The user hasn't created any tasks."

    lines = []
    pending_count = sum(1 for t in tasks if not t.completed)
    completed_count = sum(1 for t in tasks if t.completed)

    lines.append(
        f"Total: {len(tasks)} tasks ({pending_count} pending, {completed_count} completed)"
    )
    lines.append("")

    for task in tasks:
        status = "[DONE]" if task.completed else "[TODO]"
        desc = f" - {task.description}" if task.description else ""
        lines.append(f"- ID: {task.id}")
        lines.append(f"  Title: {task.title}")
        lines.append(f"  Status: {status}")
        if desc:
            lines.append(f"  Description: {task.description}")
        lines.append("")

    return "\n".join(lines)


def build_system_prompt(tasks: list[Task]) -> str:
    """Build the complete system prompt with current task context.

    Args:
        tasks: List of user's tasks.

    Returns:
        Complete system prompt string.
    """
    task_context = format_task_context(tasks)
    return SYSTEM_PROMPT_TEMPLATE.format(task_context=task_context)
