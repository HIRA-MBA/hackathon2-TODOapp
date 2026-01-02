"""Command handlers for CLI operations."""

from src.cli import display
from src.cli.parser import parse_task_id
from src.services.task_service import TaskService


def handle_add(service: TaskService) -> None:
    """Handle add command: prompt for title and description, create task."""
    # Prompt for title (required)
    while True:
        title = input("Enter task title: ")
        if title and title.strip():
            break
        print(display.show_title_empty())

    # Prompt for description (optional)
    description = input("Enter description (optional, press Enter to skip): ")
    if not description.strip():
        description = None

    task = service.add_task(title, description)
    if task:
        print(display.show_add_confirmation(task))
    else:
        print(display.show_title_empty())


def handle_view(service: TaskService) -> None:
    """Handle view command: display all tasks."""
    tasks = service.get_all_tasks()
    print(display.format_task_list(tasks))


def handle_toggle(service: TaskService) -> None:
    """Handle toggle command: prompt for ID and toggle completion status."""
    task_id = _prompt_for_task_id()
    if task_id is None:
        return

    task = service.toggle_task(task_id)
    if task:
        print(display.show_toggle_confirmation(task))
    else:
        print(display.show_task_not_found())


def handle_update(service: TaskService) -> None:
    """Handle update command: prompt for ID and new values."""
    task_id = _prompt_for_task_id()
    if task_id is None:
        return

    # Check if task exists first
    existing = service.get_task(task_id)
    if existing is None:
        print(display.show_task_not_found())
        return

    # Prompt for new title (Enter to keep current)
    print(f'Current title: "{existing.title}"')
    new_title = input("Enter new title (press Enter to keep current): ")
    if not new_title.strip():
        new_title = None

    # Prompt for new description (Enter to keep current)
    current_desc = existing.description or "(none)"
    print(f'Current description: "{current_desc}"')
    new_description = input("Enter new description (press Enter to keep current): ")
    if not new_description.strip():
        new_description = None

    task = service.update_task(task_id, new_title, new_description)
    if task:
        print(display.show_update_confirmation(task))


def handle_delete(service: TaskService) -> None:
    """Handle delete command: prompt for ID and delete task."""
    task_id = _prompt_for_task_id()
    if task_id is None:
        return

    if service.delete_task(task_id):
        print(display.show_delete_confirmation(task_id))
    else:
        print(display.show_task_not_found())


def handle_exit() -> bool:
    """Handle exit command: display goodbye and return exit signal."""
    print(display.show_goodbye())
    return True


def handle_unknown() -> None:
    """Handle unknown command: show error with available commands."""
    print(display.show_unknown_command())


def _prompt_for_task_id() -> int | None:
    """Prompt user for task ID with validation."""
    user_input = input("Enter task ID: ")
    task_id = parse_task_id(user_input)

    if task_id is None:
        print(display.show_invalid_id())
        return None

    return task_id
