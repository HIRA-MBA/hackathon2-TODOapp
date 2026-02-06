"""Event models for Dapr pub/sub (CloudEvents format).

Per data-model.md and contracts/task-events.yaml:
- TaskEvent: Domain events for task CRUD operations
- ReminderEvent: Scheduled notification triggers

All events use CloudEvents 1.0 specification envelope.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskEventType(str, Enum):
    """Task event types per data-model.md."""
    CREATED = "com.todo.task.created"
    UPDATED = "com.todo.task.updated"
    DELETED = "com.todo.task.deleted"
    COMPLETED = "com.todo.task.completed"


class ReminderEventType(str, Enum):
    """Reminder event types."""
    TRIGGER = "com.todo.reminder.trigger"
    CANCELLED = "com.todo.reminder.cancelled"


class TaskEventData(BaseModel):
    """Payload data for task events.

    Contains a snapshot of the task at event time.
    """
    task_id: UUID
    title: str
    description: str | None = None
    completed: bool
    priority: str
    due_date: datetime | None = None
    user_id: str
    recurrence_id: UUID | None = None
    parent_task_id: UUID | None = None
    reminder_offset: int = 30


class TaskEvent(BaseModel):
    """CloudEvents envelope for task events.

    Per CloudEvents spec 1.0:
    https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
    """
    # Required CloudEvents attributes
    specversion: str = Field(default="1.0", description="CloudEvents spec version")
    id: UUID = Field(default_factory=uuid4, description="Event ID (idempotency key)")
    source: str = Field(
        default="https://api.todo.example.com/tasks",
        description="Event source identifier",
    )
    type: TaskEventType = Field(description="Event type")

    # Optional CloudEvents attributes
    datacontenttype: str = Field(default="application/json")
    subject: str = Field(description="Subject (e.g., 'tasks/{task_id}')")
    time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

    # Extension attributes for distributed tracing
    correlationid: str | None = Field(default=None, description="Distributed trace correlation ID")

    # Event payload
    data: TaskEventData


class ReminderEventData(BaseModel):
    """Payload data for reminder events."""
    task_id: UUID
    task_title: str
    user_id: str
    due_date: datetime
    scheduled_time: datetime = Field(description="When reminder was scheduled to trigger")
    channels: list[str] = Field(
        default_factory=lambda: ["email"],
        description="Notification channels: email, push",
    )


class ReminderEvent(BaseModel):
    """CloudEvents envelope for reminder events."""
    # Required CloudEvents attributes
    specversion: str = Field(default="1.0")
    id: UUID = Field(default_factory=uuid4)
    source: str = Field(default="https://api.todo.example.com/reminders")
    type: ReminderEventType = Field(description="Event type")

    # Optional CloudEvents attributes
    datacontenttype: str = Field(default="application/json")
    subject: str = Field(description="Subject (e.g., 'reminders/{task_id}')")
    time: datetime = Field(default_factory=datetime.utcnow)

    # Extension attributes
    correlationid: str | None = Field(default=None)

    # Event payload
    data: ReminderEventData


# Factory functions for creating events
def create_task_event(
    event_type: TaskEventType,
    task_id: UUID,
    title: str,
    user_id: str,
    completed: bool = False,
    priority: str = "medium",
    description: str | None = None,
    due_date: datetime | None = None,
    recurrence_id: UUID | None = None,
    parent_task_id: UUID | None = None,
    reminder_offset: int = 30,
    correlation_id: str | None = None,
) -> TaskEvent:
    """Create a TaskEvent with proper CloudEvents envelope."""
    return TaskEvent(
        type=event_type,
        subject=f"tasks/{task_id}",
        correlationid=correlation_id,
        data=TaskEventData(
            task_id=task_id,
            title=title,
            description=description,
            completed=completed,
            priority=priority,
            due_date=due_date,
            user_id=user_id,
            recurrence_id=recurrence_id,
            parent_task_id=parent_task_id,
            reminder_offset=reminder_offset,
        ),
    )


def create_reminder_event(
    task_id: UUID,
    task_title: str,
    user_id: str,
    due_date: datetime,
    scheduled_time: datetime,
    channels: list[str] | None = None,
    correlation_id: str | None = None,
) -> ReminderEvent:
    """Create a ReminderEvent with proper CloudEvents envelope."""
    return ReminderEvent(
        type=ReminderEventType.TRIGGER,
        subject=f"reminders/{task_id}",
        correlationid=correlation_id,
        data=ReminderEventData(
            task_id=task_id,
            task_title=task_title,
            user_id=user_id,
            due_date=due_date,
            scheduled_time=scheduled_time,
            channels=channels or ["email"],
        ),
    )
