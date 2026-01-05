from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Request schema for creating a new task.

    Note: user_id is NOT included - it comes from JWT token only.
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)


class TaskUpdate(BaseModel):
    """Request schema for updating a task.

    All fields are optional - only provided fields are updated.
    """

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)


class TaskResponse(BaseModel):
    """Response schema for a single task."""

    id: UUID
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response schema for a list of tasks."""

    tasks: list[TaskResponse]
    count: int
