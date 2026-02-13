"""Task model with Phase V recurrence support.

Extended from Phase IV to support:
- Recurring task patterns (FR-013)
- Reminder offsets for notifications (FR-016)
- Parent-child relationships for recurring instances
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.recurrence import RecurrencePattern


class Priority(str, Enum):
    """Task priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(SQLModel, table=True):
    """Task entity representing a todo item belonging to a user.

    Per data-model.md:
    - Each task belongs to exactly one user (user_id from JWT claims)
    - Tasks are ordered by created_at DESC (newest first)
    - user_id is NEVER accepted from client input

    Phase V additions:
    - recurrence_id: Links to RecurrencePattern for recurring tasks
    - parent_task_id: Self-reference for recurring instances
    - reminder_offset: Minutes before due_date for reminder notification

    Note: user_id is a string (not UUID) because Better Auth generates
    non-UUID string IDs like '7OMgLqJ4nHFamYC3ojPQLGv0yBoUmBrS'.
    """

    __tablename__ = "task"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(max_length=64, index=True, nullable=False)
    title: str = Field(max_length=200, nullable=False)
    description: str | None = Field(default=None)
    completed: bool = Field(default=False)
    priority: str = Field(default="medium")  # high, medium, low
    due_date: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Phase V: Recurrence support
    recurrence_id: UUID | None = Field(
        default=None,
        foreign_key="recurrence_pattern.id",
        description="Recurrence pattern for this task",
    )
    parent_task_id: UUID | None = Field(
        default=None,
        foreign_key="task.id",
        index=True,
        description="Original task if this is a recurring instance",
    )
    reminder_offset: int = Field(
        default=30,
        ge=0,
        description="Minutes before due_date to trigger reminder",
    )

    # Relationships
    recurrence: Optional["RecurrencePattern"] = Relationship(back_populates="tasks")
    # Note: parent_task relationship handled via sa_relationship_kwargs for self-reference
