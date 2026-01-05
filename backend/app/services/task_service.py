from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service for task CRUD operations with user-scoped queries.

    Per data-model.md Security Invariants:
    - user_id source: Only from validated JWT 'sub' claim
    - No unscoped queries: All queries MUST include user_id filter
    - Return 404 not 403: Prevents user enumeration attacks

    Note: user_id is a string (not UUID) because Better Auth generates
    non-UUID string IDs like '7OMgLqJ4nHFamYC3ojPQLGv0yBoUmBrS'.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_tasks(self, user_id: str) -> list[Task]:
        """List all tasks for a user, ordered by created_at DESC.

        Per FR-012a: Return tasks ordered by created_at DESC (newest first).
        """
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_task(self, task_id: UUID, user_id: str) -> Task | None:
        """Get a single task by ID for a specific user.

        Returns None if task doesn't exist OR doesn't belong to user.
        Per FR-018: Return 404 (not 403) for other users' tasks.
        """
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_task(self, user_id: str, data: TaskCreate) -> Task:
        """Create a new task for a user.

        Per FR-016: user_id comes from JWT, never from client input.
        """
        task = Task(
            user_id=user_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            completed=False,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def update_task(
        self, task_id: UUID, user_id: str, data: TaskUpdate
    ) -> Task | None:
        """Update a task's title and/or description.

        Only updates fields that are provided (not None).
        Returns None if task doesn't exist or doesn't belong to user.
        """
        # Build update values from provided fields
        values: dict = {"updated_at": datetime.utcnow()}
        if data.title is not None:
            values["title"] = data.title.strip()
        if data.description is not None:
            values["description"] = data.description.strip() if data.description else None

        stmt = (
            update(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .values(**values)
            .returning(Task)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def toggle_task(self, task_id: UUID, user_id: str) -> Task | None:
        """Toggle a task's completion status.

        Returns the updated task or None if not found/not owned.
        """
        # First get current state
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        # Toggle and update
        stmt = (
            update(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .values(completed=not task.completed, updated_at=datetime.utcnow())
            .returning(Task)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_task(self, task_id: UUID, user_id: str) -> bool:
        """Delete a task.

        Returns True if deleted, False if not found/not owned.
        """
        stmt = delete(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
