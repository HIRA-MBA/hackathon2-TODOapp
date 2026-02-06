"""RecurrencePattern model for recurring task schedules.

Per data-model.md: Defines repeat schedule for recurring tasks (FR-013).
Supports daily, weekly, monthly, and custom (RFC 5545 RRULE) patterns.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import Integer
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.task import Task


class RecurrenceFrequency(str, Enum):
    """Recurrence frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Uses rrule_string


class RecurrencePattern(SQLModel, table=True):
    """Recurrence pattern for recurring tasks.

    Validation rules per data-model.md:
    - Either end_date OR max_occurrences MUST be set (not both, not neither)
    - interval must be >= 1
    - by_weekday values must be 0-6 (Mon=0, Sun=6)
    - by_monthday must be 1-31
    """

    __tablename__ = "recurrence_pattern"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    frequency: RecurrenceFrequency = Field(nullable=False)
    interval: int = Field(default=1, ge=1, description="Every N frequency units")

    # For weekly recurrence: days of week (0=Mon, 6=Sun)
    by_weekday: list[int] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Integer), nullable=True),
    )

    # For monthly recurrence: day of month (1-31)
    by_monthday: int | None = Field(default=None, ge=1, le=31)

    # End conditions (exactly one must be set)
    end_date: datetime | None = Field(default=None)
    max_occurrences: int | None = Field(default=None, ge=1)

    # RFC 5545 RRULE for complex patterns (used when frequency=custom)
    rrule_string: str | None = Field(default=None, max_length=500)

    # Relationships
    tasks: List["Task"] = Relationship(back_populates="recurrence")
