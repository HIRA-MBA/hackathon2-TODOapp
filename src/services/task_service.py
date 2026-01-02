"""Task service - business logic for task operations."""

from src.models.task import Task, TaskStore


class TaskService:
    """Service layer for task operations with validation."""

    def __init__(self, store: TaskStore | None = None) -> None:
        """Initialize service with optional store (creates new one if not provided)."""
        self._store = store if store is not None else TaskStore()

    def add_task(self, title: str, description: str | None = None) -> Task | None:
        """Add a new task with title validation.

        Returns the new Task if successful, None if title is empty/whitespace.
        """
        if not title or not title.strip():
            return None

        return self._store.add(title.strip(), description)

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks."""
        return self._store.get_all()

    def get_task(self, task_id: int) -> Task | None:
        """Return task by ID or None if not found."""
        return self._store.get_by_id(task_id)

    def update_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
    ) -> Task | None:
        """Update task fields. Returns updated task or None if not found."""
        return self._store.update(task_id, title, description)

    def delete_task(self, task_id: int) -> bool:
        """Delete task by ID. Returns True if deleted, False if not found."""
        return self._store.delete(task_id)

    def toggle_task(self, task_id: int) -> Task | None:
        """Toggle task completion. Returns updated task or None if not found."""
        return self._store.toggle(task_id)
