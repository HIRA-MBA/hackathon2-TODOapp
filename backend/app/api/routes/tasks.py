"""Task API routes with Phase V recurrence support.

Per api-extensions.yaml: Extended task endpoints with recurrence management.
Per T032-T033: Includes recurrence CRUD and recurring instances endpoints.
"""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.auth import CurrentUser
from app.models.recurrence import RecurrencePattern, RecurrenceFrequency
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskCompleteResponse,
    RecurrencePatternCreate,
    RecurrencePatternResponse,
    RecurringInstancesResponse,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    """Dependency to get TaskService instance."""
    return TaskService(session)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def _create_recurrence_model(data: RecurrencePatternCreate) -> RecurrencePattern:
    """Convert schema to SQLModel."""
    return RecurrencePattern(
        frequency=RecurrenceFrequency(data.frequency),
        interval=data.interval,
        by_weekday=data.by_weekday,
        by_monthday=data.by_monthday,
        end_date=data.end_date,
        max_occurrences=data.max_occurrences,
        rrule_string=data.rrule_string,
    )


def _task_to_response(task) -> TaskResponse:
    """Convert Task model to response schema."""
    recurrence_response = None
    if task.recurrence:
        recurrence_response = RecurrencePatternResponse.model_validate(task.recurrence)

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        priority=task.priority,
        due_date=task.due_date,
        reminder_offset=task.reminder_offset,
        recurrence_id=task.recurrence_id,
        parent_task_id=task.parent_task_id,
        has_recurrence=task.recurrence_id is not None,
        recurrence=recurrence_response,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# Task CRUD Endpoints

@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user: CurrentUser,
    service: TaskServiceDep,
    sort_by: Literal["created_at", "due_date"] = Query(
        default="created_at",
        description="Sort order: 'created_at' (newest first) or 'due_date' (soonest first)",
    ),
):
    """List all tasks for authenticated user.

    Supports sorting by created_at (default) or due_date.
    """
    tasks = await service.list_tasks(user.user_id, sort_by=sort_by)
    return TaskListResponse(
        tasks=[_task_to_response(t) for t in tasks],
        count=len(tasks),
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Create a new task for authenticated user.

    Per FR-016: user_id comes from JWT, never from client input.
    Per T026: Publishes task.created event to Dapr pub/sub.
    """
    recurrence = None
    if data.recurrence:
        # Validate end condition
        if data.recurrence.end_date is None and data.recurrence.max_occurrences is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence must have either end_date or max_occurrences",
            )
        if data.recurrence.end_date is not None and data.recurrence.max_occurrences is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recurrence cannot have both end_date and max_occurrences",
            )
        recurrence = _create_recurrence_model(data.recurrence)

    task = await service.create_task(user.user_id, data, recurrence)
    return _task_to_response(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Get a specific task by ID.

    Per FR-018: Returns 404 (not 403) for other users' tasks.
    """
    task = await service.get_task(task_id, user.user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return _task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Update a task's fields.

    Per T027: Publishes task.updated event to Dapr pub/sub.
    """
    task = await service.update_task(task_id, user.user_id, data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return _task_to_response(task)


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Toggle a task's completion status.

    Per T029: Publishes task.completed event when completing.
    """
    task = await service.toggle_task(task_id, user.user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return _task_to_response(task)


@router.post("/{task_id}/complete", response_model=TaskCompleteResponse)
async def complete_task(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Mark task as completed.

    Per api-extensions.yaml: Triggers recurring task creation if recurrence exists.
    Publishes task.completed event which the recurring-task service consumes.
    """
    task = await service.complete_task(task_id, user.user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or already completed",
        )

    # Build response with next instance info (async creation via event)
    next_instance = None
    if task.recurrence_id:
        # The actual next instance is created asynchronously by recurring-task service
        # We just indicate that one is scheduled
        next_instance = {
            "scheduledFor": "pending",  # Actual date computed by recurring-task service
            "message": "Next instance will be created by recurring-task service",
        }

    return TaskCompleteResponse(
        task=_task_to_response(task),
        next_instance=next_instance,
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Delete a task permanently.

    Per T028: Publishes task.deleted event to Dapr pub/sub.
    """
    deleted = await service.delete_task(task_id, user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return None


# Recurrence Endpoints (T033)

@router.get("/{task_id}/recurrence", response_model=RecurrencePatternResponse)
async def get_task_recurrence(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Get the recurrence pattern for a task."""
    recurrence = await service.get_task_recurrence(task_id, user.user_id)
    if not recurrence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or has no recurrence pattern",
        )
    return RecurrencePatternResponse.model_validate(recurrence)


@router.put("/{task_id}/recurrence", response_model=RecurrencePatternResponse)
async def set_task_recurrence(
    task_id: UUID,
    data: RecurrencePatternCreate,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Set or update the recurrence pattern for a task."""
    # Validate end condition
    if data.end_date is None and data.max_occurrences is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recurrence must have either end_date or max_occurrences",
        )
    if data.end_date is not None and data.max_occurrences is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recurrence cannot have both end_date and max_occurrences",
        )

    recurrence = _create_recurrence_model(data)
    result = await service.set_task_recurrence(task_id, user.user_id, recurrence)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return RecurrencePatternResponse.model_validate(result)


@router.delete("/{task_id}/recurrence", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task_recurrence(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Remove recurrence pattern from a task."""
    removed = await service.remove_task_recurrence(task_id, user.user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or has no recurrence pattern",
        )
    return None


@router.get("/{task_id}/instances", response_model=RecurringInstancesResponse)
async def get_recurring_instances(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
    task_status: Literal["pending", "completed", "all"] = Query(
        default="all",
        alias="status",
        description="Filter by completion status",
    ),
    limit: int = Query(default=50, le=100, description="Maximum instances to return"),
):
    """Get all instances of a recurring task.

    Returns tasks that have this task as their parent_task_id.
    """
    # Verify the parent task exists and belongs to user
    parent = await service.get_task(task_id, user.user_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    instances = await service.get_recurring_instances(
        task_id, user.user_id, status=task_status, limit=limit
    )

    return RecurringInstancesResponse(
        parent_task_id=task_id,
        instances=[_task_to_response(t) for t in instances],
        total=len(instances),
    )
