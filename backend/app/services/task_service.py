"""Task Service with event publishing for Phase V.

Per plan.md: Integrates event publisher for task CRUD operations.
Events are published asynchronously without blocking user interaction.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.recurrence import RecurrencePattern
from app.models.events import TaskEventType, create_task_event
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.event_publisher import get_event_publisher
from app.middleware.correlation import get_correlation_id

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task CRUD operations with event publishing.

    Per data-model.md Security Invariants:
    - user_id source: Only from validated JWT 'sub' claim
    - No unscoped queries: All queries MUST include user_id filter
    - Return 404 not 403: Prevents user enumeration attacks

    Phase V: All mutations publish events to Dapr pub/sub.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._event_publisher = get_event_publisher()

    async def _publish_task_event(
        self,
        event_type: TaskEventType,
        task: Task,
    ) -> None:
        """Publish a task event asynchronously.

        Per T030-T031: Includes retry/fallback and correlation ID propagation.
        """
        try:
            event = create_task_event(
                event_type=event_type,
                task_id=task.id,
                title=task.title,
                user_id=task.user_id,
                completed=task.completed,
                priority=task.priority,
                description=task.description,
                due_date=task.due_date,
                recurrence_id=task.recurrence_id,
                parent_task_id=task.parent_task_id,
                reminder_offset=task.reminder_offset,
                correlation_id=get_correlation_id(),
            )

            success = await self._event_publisher.publish_task_event(event)

            if success:
                logger.info(
                    "task_event_published",
                    extra={
                        "event_type": event_type.value,
                        "task_id": str(task.id),
                        "user_id": task.user_id,
                    },
                )
            else:
                logger.warning(
                    "task_event_publish_failed_queued",
                    extra={
                        "event_type": event_type.value,
                        "task_id": str(task.id),
                    },
                )
        except Exception as e:
            # Don't fail the operation if event publishing fails
            logger.error(
                "task_event_publish_error",
                extra={
                    "event_type": event_type.value,
                    "task_id": str(task.id),
                    "error": str(e),
                },
            )

    async def list_tasks(self, user_id: str, sort_by: str = "created_at") -> list[Task]:
        """List all tasks for a user with optional sorting.

        Args:
            user_id: The user's ID
            sort_by: Sort field - "created_at" (default, newest first) or "due_date" (soonest first)
        """
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .options(selectinload(Task.recurrence))
        )

        if sort_by == "due_date":
            stmt = stmt.order_by(
                Task.due_date.asc().nulls_last(), Task.created_at.desc()
            )
        else:
            stmt = stmt.order_by(Task.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_task(self, task_id: UUID, user_id: str) -> Task | None:
        """Get a single task by ID for a specific user.

        Returns None if task doesn't exist OR doesn't belong to user.
        """
        stmt = (
            select(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .options(selectinload(Task.recurrence))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_task(
        self,
        user_id: str,
        data: TaskCreate,
        recurrence: RecurrencePattern | None = None,
    ) -> Task:
        """Create a new task for a user.

        Per T026: Publishes task.created event after creation.
        """
        # Create recurrence pattern if provided
        recurrence_id = None
        if recurrence:
            self.session.add(recurrence)
            await self.session.flush()
            recurrence_id = recurrence.id

        task = Task(
            user_id=user_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            completed=False,
            priority=data.priority,
            due_date=data.due_date,
            reminder_offset=data.reminder_offset
            if hasattr(data, "reminder_offset") and data.reminder_offset
            else 30,
            recurrence_id=recurrence_id,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)

        # Load recurrence relationship if exists
        if recurrence_id:
            stmt = (
                select(Task)
                .where(Task.id == task.id)
                .options(selectinload(Task.recurrence))
            )
            result = await self.session.execute(stmt)
            task = result.scalar_one()

        # Publish task.created event (T026)
        await self._publish_task_event(TaskEventType.CREATED, task)

        return task

    async def update_task(
        self, task_id: UUID, user_id: str, data: TaskUpdate
    ) -> Task | None:
        """Update a task's fields.

        Per T027: Publishes task.updated event after update.
        """
        # Build update values from provided fields
        values: dict = {"updated_at": datetime.utcnow()}
        if data.title is not None:
            values["title"] = data.title.strip()
        if data.description is not None:
            values["description"] = (
                data.description.strip() if data.description else None
            )
        if data.priority is not None:
            values["priority"] = data.priority
        if data.due_date is not None:
            values["due_date"] = data.due_date
        if hasattr(data, "reminder_offset") and data.reminder_offset is not None:
            values["reminder_offset"] = data.reminder_offset

        stmt = (
            update(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .values(**values)
            .returning(Task)
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            # Reload with relationships
            stmt = (
                select(Task)
                .where(Task.id == task.id)
                .options(selectinload(Task.recurrence))
            )
            result = await self.session.execute(stmt)
            task = result.scalar_one()

            # Publish task.updated event (T027)
            await self._publish_task_event(TaskEventType.UPDATED, task)

        return task

    async def toggle_task(self, task_id: UUID, user_id: str) -> Task | None:
        """Toggle a task's completion status.

        Per T029: Publishes task.completed event when completing (triggers recurring logic).
        """
        # First get current state
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        new_completed = not task.completed

        # Toggle and update
        stmt = (
            update(Task)
            .where(Task.id == task_id, Task.user_id == user_id)
            .values(completed=new_completed, updated_at=datetime.utcnow())
            .returning(Task)
        )
        result = await self.session.execute(stmt)
        updated_task = result.scalar_one_or_none()

        if updated_task:
            # Reload with relationships
            stmt = (
                select(Task)
                .where(Task.id == updated_task.id)
                .options(selectinload(Task.recurrence))
            )
            result = await self.session.execute(stmt)
            updated_task = result.scalar_one()

            # Publish appropriate event (T029)
            if new_completed:
                await self._publish_task_event(TaskEventType.COMPLETED, updated_task)
            else:
                await self._publish_task_event(TaskEventType.UPDATED, updated_task)

        return updated_task

    async def complete_task(self, task_id: UUID, user_id: str) -> Task | None:
        """Mark a task as completed.

        Per T029: Publishes task.completed event which triggers recurring task creation.
        Separate from toggle to have explicit completion semantics.
        """
        stmt = (
            update(Task)
            .where(
                Task.id == task_id, Task.user_id == user_id, Task.completed.is_(False)
            )
            .values(completed=True, updated_at=datetime.utcnow())
            .returning(Task)
        )
        result = await self.session.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            # Reload with relationships
            stmt = (
                select(Task)
                .where(Task.id == task.id)
                .options(selectinload(Task.recurrence))
            )
            result = await self.session.execute(stmt)
            task = result.scalar_one()

            # Publish task.completed event (T029)
            await self._publish_task_event(TaskEventType.COMPLETED, task)

        return task

    async def delete_task(self, task_id: UUID, user_id: str) -> bool:
        """Delete a task.

        Per T028: Publishes task.deleted event before deletion.
        """
        # Get task before deletion for event payload
        task = await self.get_task(task_id, user_id)
        if not task:
            return False

        # Publish task.deleted event (T028)
        await self._publish_task_event(TaskEventType.DELETED, task)

        # Perform deletion
        stmt = delete(Task).where(Task.id == task_id, Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # Recurrence-related methods (T033)

    async def get_task_recurrence(
        self, task_id: UUID, user_id: str
    ) -> RecurrencePattern | None:
        """Get the recurrence pattern for a task."""
        task = await self.get_task(task_id, user_id)
        if not task or not task.recurrence_id:
            return None
        return task.recurrence

    async def set_task_recurrence(
        self,
        task_id: UUID,
        user_id: str,
        recurrence: RecurrencePattern,
    ) -> RecurrencePattern | None:
        """Set or update the recurrence pattern for a task."""
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        # If task already has recurrence, update it
        if task.recurrence_id:
            existing = await self.session.get(RecurrencePattern, task.recurrence_id)
            if existing:
                existing.frequency = recurrence.frequency
                existing.interval = recurrence.interval
                existing.by_weekday = recurrence.by_weekday
                existing.by_monthday = recurrence.by_monthday
                existing.end_date = recurrence.end_date
                existing.max_occurrences = recurrence.max_occurrences
                existing.rrule_string = recurrence.rrule_string
                await self.session.flush()
                return existing

        # Create new recurrence pattern
        self.session.add(recurrence)
        await self.session.flush()

        # Link to task
        task.recurrence_id = recurrence.id
        task.updated_at = datetime.utcnow()
        await self.session.flush()

        # Publish update event
        await self.session.refresh(task)
        await self._publish_task_event(TaskEventType.UPDATED, task)

        return recurrence

    async def remove_task_recurrence(self, task_id: UUID, user_id: str) -> bool:
        """Remove recurrence pattern from a task."""
        task = await self.get_task(task_id, user_id)
        if not task or not task.recurrence_id:
            return False

        recurrence_id = task.recurrence_id

        # Unlink from task
        task.recurrence_id = None
        task.updated_at = datetime.utcnow()
        await self.session.flush()

        # Delete the recurrence pattern
        stmt = delete(RecurrencePattern).where(RecurrencePattern.id == recurrence_id)
        await self.session.execute(stmt)

        # Publish update event
        await self._publish_task_event(TaskEventType.UPDATED, task)

        return True

    async def get_recurring_instances(
        self,
        parent_task_id: UUID,
        user_id: str,
        status: str = "all",
        limit: int = 50,
    ) -> list[Task]:
        """Get all instances of a recurring task."""
        stmt = select(Task).where(
            Task.parent_task_id == parent_task_id, Task.user_id == user_id
        )

        if status == "pending":
            stmt = stmt.where(Task.completed.is_(False))
        elif status == "completed":
            stmt = stmt.where(Task.completed.is_(True))

        stmt = stmt.order_by(Task.created_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
