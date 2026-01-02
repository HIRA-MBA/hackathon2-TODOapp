"""Display module - output formatting for CLI."""

from src.models.task import Task


def format_task(task: Task) -> str:
    """Format a single task with checkbox indicator.

    Format: [x] ID: Title
            Description: ...
    """
    checkbox = "[x]" if task.completed else "[ ]"
    result = f"{checkbox} {task.id}: {task.title}"

    if task.description:
        result += f"\n    Description: {task.description}"

    return result


def format_task_list(tasks: list[Task]) -> str:
    """Format a list of tasks for display."""
    if not tasks:
        return show_empty_list_message()

    return "\n".join(format_task(task) for task in tasks)


def show_empty_list_message() -> str:
    """Return message for empty task list."""
    return "No tasks yet. Use 'add' to create one."


def show_add_confirmation(task: Task) -> str:
    """Return confirmation message for added task."""
    return f'Task added: [{task.id}] "{task.title}"'


def show_update_confirmation(task: Task) -> str:
    """Return confirmation message for updated task."""
    return f'Task updated: [{task.id}] "{task.title}"'


def show_delete_confirmation(task_id: int) -> str:
    """Return confirmation message for deleted task."""
    return f"Task deleted: [{task_id}]"


def show_toggle_confirmation(task: Task) -> str:
    """Return confirmation message for toggled task."""
    status = "complete" if task.completed else "incomplete"
    return f"Task [{task.id}] marked as {status}"


def show_error(message: str) -> str:
    """Return formatted error message."""
    return f"Error: {message}"


def show_task_not_found() -> str:
    """Return task not found error message."""
    return show_error("Task not found")


def show_invalid_id() -> str:
    """Return invalid ID error message."""
    return show_error("Invalid ID")


def show_title_empty() -> str:
    """Return empty title error message."""
    return show_error("Title cannot be empty")


def show_unknown_command() -> str:
    """Return unknown command error with available commands."""
    return "Unknown command. Available: add, view, update, delete, toggle, exit"


def show_commands_menu() -> str:
    """Return available commands menu."""
    return """
Available commands:
  add     - Add a new task
  view    - View all tasks
  update  - Update a task
  delete  - Delete a task
  toggle  - Toggle task completion
  exit    - Exit the application
"""


def show_welcome() -> str:
    """Return welcome message."""
    return "Welcome to Todo CLI!" + show_commands_menu()


def show_continue_prompt() -> str:
    """Return continue or exit prompt."""
    return "\nPress Enter to continue or type 'exit' to quit..."


def show_goodbye() -> str:
    """Return goodbye message."""
    return "Goodbye!"
