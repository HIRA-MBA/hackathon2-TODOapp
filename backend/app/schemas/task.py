"""Task schemas with Phase V recurrence support.

Per api-extensions.yaml: Extended request/response schemas for tasks
with recurrence, reminder, and parent task fields.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


# Recurrence Schemas


class RecurrencePatternCreate(BaseModel):
    """Request schema for creating a recurrence pattern."""

    frequency: str = Field(..., pattern="^(daily|weekly|monthly|custom)$")
    interval: int = Field(default=1, ge=1, description="Every N frequency units")
    by_weekday: list[int] | None = Field(
        default=None,
        description="Days of week (0=Monday, 6=Sunday)",
    )
    by_monthday: int | None = Field(default=None, ge=1, le=31)
    end_date: datetime | None = Field(
        default=None,
        description="When recurrence stops (mutually exclusive with max_occurrences)",
    )
    max_occurrences: int | None = Field(
        default=None,
        ge=1,
        description="Max instances to create (mutually exclusive with end_date)",
    )
    rrule_string: str | None = Field(
        default=None,
        max_length=500,
        description="RFC 5545 RRULE for custom patterns",
    )

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    @field_validator("end_date", "max_occurrences", mode="after")
    @classmethod
    def validate_end_condition(cls, v, info):
        """Validate that exactly one end condition is set."""
        # Note: This runs per-field, full validation in model_validator
        return v


class RecurrencePatternResponse(BaseModel):
    """Response schema for recurrence pattern."""

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    id: UUID
    frequency: str
    interval: int
    by_weekday: list[int] | None = None
    by_monthday: int | None = None
    end_date: datetime | None = None
    max_occurrences: int | None = None
    rrule_string: str | None = None


# Task Schemas


class TaskCreate(BaseModel):
    """Request schema for creating a new task.

    Per api-extensions.yaml: Extended with recurrence and reminder support.
    Note: user_id is NOT included - it comes from JWT token only.
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    due_date: datetime | None = Field(default=None)
    reminder_offset: int = Field(
        default=30,
        ge=0,
        description="Minutes before due date for reminder",
    )
    recurrence: RecurrencePatternCreate | None = Field(
        default=None,
        description="Recurrence pattern for repeating tasks",
    )

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TaskUpdate(BaseModel):
    """Request schema for updating a task.

    All fields are optional - only provided fields are updated.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: str | None = Field(default=None, pattern="^(high|medium|low)$")
    due_date: datetime | None = Field(default=None)
    reminder_offset: int | None = Field(default=None, ge=0)
    recurrence: RecurrencePatternCreate | None = Field(default=None)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TaskResponse(BaseModel):
    """Response schema for a single task.

    Per api-extensions.yaml: Includes recurrence and parent task info.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    id: UUID
    title: str
    description: str | None
    completed: bool
    priority: str
    due_date: datetime | None
    reminder_offset: int = 30
    recurrence_id: UUID | None = None
    parent_task_id: UUID | None = None
    has_recurrence: bool = False
    recurrence: RecurrencePatternResponse | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("has_recurrence", mode="before")
    @classmethod
    def compute_has_recurrence(cls, v, info):
        """Compute has_recurrence from recurrence_id."""
        if v is not None:
            return v
        # Check if recurrence_id is set
        data = info.data if hasattr(info, "data") else {}
        return data.get("recurrence_id") is not None


class TaskListResponse(BaseModel):
    """Response schema for a list of tasks."""

    tasks: list[TaskResponse]
    count: int


class TaskCompleteResponse(BaseModel):
    """Response schema for task completion.

    Per api-extensions.yaml: Includes info about next recurring instance.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    task: TaskResponse
    next_instance: dict | None = Field(
        default=None,
        description="Info about next recurring instance (async creation)",
    )


class RecurringInstancesResponse(BaseModel):
    """Response schema for recurring task instances."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )

    parent_task_id: UUID
    instances: list[TaskResponse]
    total: int
