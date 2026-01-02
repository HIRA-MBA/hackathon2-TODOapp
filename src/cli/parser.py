"""Parser module - command parsing and validation."""


VALID_COMMANDS = {"add", "view", "update", "delete", "toggle", "exit"}


def parse_command(user_input: str) -> str | None:
    """Parse and validate command from user input.

    Returns normalized command string if valid, None if invalid.
    Commands are case-insensitive.
    """
    if not user_input:
        return None

    command = user_input.strip().lower()

    if command in VALID_COMMANDS:
        return command

    return None


def parse_task_id(user_input: str) -> int | None:
    """Parse task ID from user input.

    Returns positive integer if valid, None if invalid.
    """
    if not user_input:
        return None

    try:
        task_id = int(user_input.strip())
        if task_id <= 0:
            return None
        return task_id
    except ValueError:
        return None
