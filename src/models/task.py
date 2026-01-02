"""Task model and storage."""

from dataclasses import dataclass


@dataclass
class Task:
    """Represents a todo item."""

    id: int
    title: str
    description: str | None
    completed: bool


class TaskStore:
    """In-memory storage for tasks using dict[int, Task]."""

    def __init__(self) -> None:
        """Initialize empty task store."""
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1

    def add(self, title: str, description: str | None = None) -> Task:
        """Add a new task and return it with auto-generated ID."""
        task = Task(
            id=self._next_id,
            title=title,
            description=description,
            completed=False,
        )
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def get_all(self) -> list[Task]:
        """Return all tasks as a list."""
        return list(self._tasks.values())

    def get_by_id(self, task_id: int) -> Task | None:
        """Return task by ID or None if not found."""
        return self._tasks.get(task_id)

    def update(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
    ) -> Task | None:
        """Update task fields. Empty string keeps current value. Returns updated task or None."""
        task = self._tasks.get(task_id)
        if task is None:
            return None

        if title is not None and title != "":
            task.title = title
        if description is not None and description != "":
            task.description = description

        return task

    def delete(self, task_id: int) -> bool:
        """Delete task by ID. Returns True if deleted, False if not found."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def toggle(self, task_id: int) -> Task | None:
        """Toggle task completion status. Returns updated task or None if not found."""
        task = self._tasks.get(task_id)
        if task is None:
            return None

        task.completed = not task.completed
        return task
