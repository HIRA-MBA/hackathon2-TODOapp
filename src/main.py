"""Main entry point for Todo CLI application."""

from src.cli import commands, display
from src.cli.parser import parse_command
from src.services.task_service import TaskService


def prompt_continue() -> bool:
    """Ask user if they want to continue. Returns False if user wants to exit."""
    print(display.show_continue_prompt())
    response = input().strip().lower()
    if response == "exit":
        return False
    # Show commands menu again when continuing
    print(display.show_commands_menu())
    return True


def main() -> None:
    """Run the Todo CLI application main loop."""
    service = TaskService()

    # Welcome message
    print(display.show_welcome())

    # Main loop
    while True:
        try:
            user_input = input("Enter command > ")

            # Handle empty input
            if not user_input.strip():
                continue

            command = parse_command(user_input)

            if command is None:
                commands.handle_unknown()
                continue

            # Handle exit immediately
            if command == "exit":
                if commands.handle_exit():
                    break
                continue

            # Dispatch to appropriate handler
            match command:
                case "add":
                    commands.handle_add(service)
                case "view":
                    commands.handle_view(service)
                case "toggle":
                    commands.handle_toggle(service)
                case "update":
                    commands.handle_update(service)
                case "delete":
                    commands.handle_delete(service)

            # After each operation, ask if user wants to continue
            if not prompt_continue():
                commands.handle_exit()
                break

        except KeyboardInterrupt:
            print()  # Newline after ^C
            if commands.handle_exit():
                break
        except EOFError:
            print()  # Newline
            if commands.handle_exit():
                break


if __name__ == "__main__":
    main()
