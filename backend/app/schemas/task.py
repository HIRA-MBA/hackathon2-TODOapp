from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class TaskCreate(BaseModel):
    """Request schema for creating a new task.

    Note: user_id is NOT included - it comes from JWT token only.
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    due_date: datetime | None = Field(None)


class TaskUpdate(BaseModel):
    """Request schema for updating a task.

    All fields are optional - only provided fields are updated.
    """

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    priority: str | None = Field(None, pattern="^(high|medium|low)$")
    due_date: datetime | None = Field(None)


class TaskResponse(BaseModel):
    """Response schema for a single task."""

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
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Response schema for a list of tasks."""

    tasks: list[TaskResponse]
    count: int
