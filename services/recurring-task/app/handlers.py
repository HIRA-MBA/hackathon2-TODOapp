"""Event handlers for recurring task service.

Per T066-T068: Handles task.completed events with idempotent processing.
Creates next task instances via backend API.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from app.recurrence import (
    RecurrencePattern,
    RecurrenceFrequency,
    calculate_next_occurrence,
    calculate_due_date_for_instance,
)

logger = logging.getLogger("recurring-task-service")

# Backend API URL
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# In-memory processed events set (for development)
# In production, use Redis or database via Dapr state store
_processed_events: set[str] = set()


class TaskData(BaseModel):
    """Task data from event payload."""
    id: str
    user_id: str = Field(alias="userId")
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = Field(None, alias="dueDate")
    reminder_offset: int = Field(30, alias="reminderOffset")
    recurrence_id: Optional[str] = Field(None, alias="recurrenceId")
    parent_task_id: Optional[str] = Field(None, alias="parentTaskId")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")

    class Config:
        populate_by_name = True


class RecurrenceData(BaseModel):
    """Recurrence pattern from event payload."""
    id: str
    frequency: str
    interval: int = 1
    by_weekday: Optional[list[int]] = Field(None, alias="byWeekday")
    by_monthday: Optional[int] = Field(None, alias="byMonthday")
    end_date: Optional[datetime] = Field(None, alias="endDate")
    max_occurrences: Optional[int] = Field(None, alias="maxOccurrences")
    rrule_string: Optional[str] = Field(None, alias="rruleString")

    class Config:
        populate_by_name = True

    def to_pattern(self) -> RecurrencePattern:
        """Convert to RecurrencePattern for calculation."""
        return RecurrencePattern(
            id=self.id,
            frequency=RecurrenceFrequency(self.frequency),
            interval=self.interval,
            by_weekday=self.by_weekday,
            by_monthday=self.by_monthday,
            end_date=self.end_date,
            max_occurrences=self.max_occurrences,
            rrule_string=self.rrule_string,
        )


class TaskCompletedEvent(BaseModel):
    """CloudEvents envelope for task.completed event."""
    id: str
    type: str
    source: str
    specversion: str = "1.0"
    time: Optional[datetime] = None
    data: dict

    def get_task_data(self) -> Optional[TaskData]:
        """Extract task data from event."""
        try:
            task_dict = self.data.get("task", self.data)
            return TaskData.model_validate(task_dict)
        except Exception as e:
            logger.error(f"Failed to parse task data: {e}")
            return None

    def get_recurrence_data(self) -> Optional[RecurrenceData]:
        """Extract recurrence pattern from event."""
        try:
            recurrence = self.data.get("recurrence")
            if not recurrence:
                return None
            return RecurrenceData.model_validate(recurrence)
        except Exception as e:
            logger.error(f"Failed to parse recurrence data: {e}")
            return None


async def is_event_processed(event_id: str) -> bool:
    """Check if event has already been processed (idempotency).

    Per T067: Uses ProcessedEvent tracking for idempotent processing.

    In production, this should use Dapr state store or database.
    """
    return event_id in _processed_events


async def mark_event_processed(event_id: str) -> None:
    """Mark event as processed.

    Per T067: Stores event ID to prevent duplicate processing.
    """
    _processed_events.add(event_id)

    # Cleanup old events (keep last 10000)
    if len(_processed_events) > 10000:
        # Remove oldest entries (in real impl, use TTL in state store)
        to_remove = list(_processed_events)[:5000]
        for item in to_remove:
            _processed_events.discard(item)


async def handle_task_completed(event: TaskCompletedEvent) -> dict:
    """Handle task.completed event and create next recurring instance.

    Per T066: Main handler for task.completed events.
    Per T068: Creates new task instance via backend API call.

    Returns:
        Processing result with status and details
    """
    event_id = event.id
    logger.info(f"Processing task.completed event: {event_id}")

    # Idempotency check
    if await is_event_processed(event_id):
        logger.info(f"Event {event_id} already processed, skipping")
        return {"status": "SKIPPED", "reason": "already_processed"}

    # Extract task and recurrence data
    task_data = event.get_task_data()
    if not task_data:
        logger.error(f"Could not extract task data from event {event_id}")
        return {"status": "ERROR", "reason": "invalid_task_data"}

    recurrence_data = event.get_recurrence_data()
    if not recurrence_data:
        logger.info(f"Task {task_data.id} has no recurrence pattern, skipping")
        await mark_event_processed(event_id)
        return {"status": "SKIPPED", "reason": "no_recurrence"}

    # Calculate next occurrence
    pattern = recurrence_data.to_pattern()
    completed_at = task_data.completed_at or datetime.utcnow()

    # Get occurrences count (would need to query backend in production)
    occurrences_count = 0  # TODO: Get from backend API

    next_occurrence = calculate_next_occurrence(
        pattern=pattern,
        last_completed=completed_at,
        occurrences_count=occurrences_count,
    )

    if not next_occurrence:
        logger.info(f"Recurrence ended for task {task_data.id}")
        await mark_event_processed(event_id)
        return {"status": "COMPLETED", "reason": "recurrence_ended"}

    # Calculate due date for new instance
    new_due_date = calculate_due_date_for_instance(
        original_due_date=task_data.due_date,
        original_completed=completed_at,
        next_occurrence=next_occurrence,
    )

    # Create new task instance via backend API
    try:
        new_task = await create_task_instance(
            user_id=task_data.user_id,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            due_date=new_due_date,
            reminder_offset=task_data.reminder_offset,
            recurrence_id=recurrence_data.id,
            parent_task_id=task_data.id,
        )

        await mark_event_processed(event_id)

        logger.info(
            f"Created recurring instance {new_task.get('id')} "
            f"for task {task_data.id}, due: {new_due_date}"
        )

        return {
            "status": "SUCCESS",
            "new_task_id": new_task.get("id"),
            "next_due_date": new_due_date.isoformat() if new_due_date else None,
        }

    except Exception as e:
        logger.error(f"Failed to create recurring instance: {e}")
        # Don't mark as processed - allow retry
        return {"status": "ERROR", "reason": str(e)}


async def create_task_instance(
    user_id: str,
    title: str,
    description: Optional[str],
    priority: str,
    due_date: Optional[datetime],
    reminder_offset: int,
    recurrence_id: str,
    parent_task_id: str,
) -> dict:
    """Create a new task instance via backend API.

    Per T068: Uses backend API to create the new task.
    The backend will handle user authorization via service-to-service auth.
    """
    # Prepare task payload
    payload = {
        "title": title,
        "description": description,
        "priority": priority,
        "reminderOffset": reminder_offset,
    }

    if due_date:
        payload["dueDate"] = due_date.isoformat()

    # Internal service call with user context
    # In production, use service-to-service auth token
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Service": "recurring-task-service",
        "X-User-Id": user_id,
        "X-Parent-Task-Id": parent_task_id,
        "X-Recurrence-Id": recurrence_id,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/api/tasks",
            json=payload,
            headers=headers,
        )

        if response.status_code not in (200, 201):
            error_msg = f"Backend returned {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)

        return response.json()
