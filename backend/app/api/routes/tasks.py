from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.auth import CurrentUser
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    """Dependency to get TaskService instance."""
    return TaskService(session)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user: CurrentUser,
    service: TaskServiceDep,
):
    """List all tasks for authenticated user.

    Per FR-012a: Returns tasks ordered by created_at DESC (newest first).
    """
    tasks = await service.list_tasks(user.user_id)
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
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
    """
    task = await service.create_task(user.user_id, data)
    return TaskResponse.model_validate(task)


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
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Update a task's title and/or description."""
    task = await service.update_task(task_id, user.user_id, data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Toggle a task's completion status."""
    task = await service.toggle_task(task_id, user.user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    user: CurrentUser,
    service: TaskServiceDep,
):
    """Delete a task permanently."""
    deleted = await service.delete_task(task_id, user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return None
