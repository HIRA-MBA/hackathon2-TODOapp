"""Reminder scheduling logic for notification service.

Per T080: Scans tasks with due dates and publishes reminder events
at the configured offset before the due date.

This module provides:
- Periodic scanning of tasks approaching their due dates
- Reminder event publishing via Dapr pub/sub
- Deduplication to avoid sending duplicate reminders
- Configurable scan interval and default reminder offset
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

logger = logging.getLogger("notification-service.scheduler")

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
DAPR_HTTP_PORT = os.environ.get("DAPR_HTTP_PORT", "3500")
DAPR_PUBSUB_NAME = os.environ.get("DAPR_PUBSUB_NAME", "pubsub")
SCAN_INTERVAL_SECONDS = int(os.environ.get("REMINDER_SCAN_INTERVAL", "60"))
DEFAULT_REMINDER_OFFSET_MINUTES = int(os.environ.get("DEFAULT_REMINDER_OFFSET", "30"))

# Track sent reminders to avoid duplicates (task_id -> last_sent_time)
_sent_reminders: dict[str, datetime] = {}

# Maximum age for sent reminder tracking entries (cleanup threshold)
_MAX_TRACKING_AGE = timedelta(hours=24)


async def fetch_upcoming_tasks(
    lookahead_minutes: int = 60,
) -> list[dict]:
    """Fetch tasks with due dates within the lookahead window.

    Queries the backend API for tasks due within the next N minutes.

    Args:
        lookahead_minutes: How far ahead to look for upcoming tasks.

    Returns:
        List of task dicts from the backend API.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            now = datetime.now(timezone.utc)
            window_end = now + timedelta(minutes=lookahead_minutes)

            response = await client.get(
                f"{BACKEND_URL}/api/tasks",
                params={
                    "due_before": window_end.isoformat(),
                    "completed": "false",
                },
                headers={"X-Internal-Service": "notification-scheduler"},
            )

            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                # Filter to tasks with due dates in the window
                upcoming = []
                for task in tasks:
                    due_date_str = task.get("dueDate") or task.get("due_date")
                    if not due_date_str:
                        continue
                    try:
                        due_date = datetime.fromisoformat(
                            due_date_str.replace("Z", "+00:00")
                        )
                        if now < due_date <= window_end:
                            upcoming.append(task)
                    except (ValueError, TypeError):
                        continue
                return upcoming
            else:
                logger.warning(
                    "Failed to fetch tasks from backend",
                    extra={"status_code": response.status_code},
                )
                return []

    except Exception as e:
        logger.error("Error fetching upcoming tasks", extra={"error": str(e)})
        return []


def should_send_reminder(
    task_id: str,
    due_date: datetime,
    reminder_offset_minutes: int,
) -> bool:
    """Determine if a reminder should be sent for this task.

    Checks:
    1. Whether the reminder window has been reached
    2. Whether a reminder was already sent for this task

    Args:
        task_id: The task identifier.
        due_date: When the task is due.
        reminder_offset_minutes: Minutes before due date to send reminder.

    Returns:
        True if a reminder should be sent.
    """
    now = datetime.now(timezone.utc)
    reminder_time = due_date - timedelta(minutes=reminder_offset_minutes)

    # Not yet time for the reminder
    if now < reminder_time:
        return False

    # Already past due - don't send reminder
    if now > due_date:
        return False

    # Already sent a reminder for this task
    if task_id in _sent_reminders:
        return False

    return True


async def publish_reminder_event(task: dict) -> bool:
    """Publish a reminder event to Dapr pub/sub.

    Args:
        task: Task dict from backend API.

    Returns:
        True if published successfully.
    """
    task_id = str(task.get("id", ""))
    task_title = task.get("title", "Untitled Task")
    user_id = task.get("userId") or task.get("user_id", "")
    due_date_str = task.get("dueDate") or task.get("due_date", "")
    reminder_offset = task.get("reminderOffset") or task.get(
        "reminder_offset", DEFAULT_REMINDER_OFFSET_MINUTES
    )

    try:
        due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        logger.error(f"Invalid due_date for task {task_id}: {due_date_str}")
        return False

    event = {
        "specversion": "1.0",
        "type": "com.todo.reminder.trigger",
        "source": "https://api.todo.example.com/scheduler",
        "subject": f"reminders/{task_id}",
        "datacontenttype": "application/json",
        "data": {
            "taskId": task_id,
            "taskTitle": task_title,
            "userId": user_id,
            "dueDate": due_date.isoformat(),
            "scheduledTime": datetime.now(timezone.utc).isoformat(),
            "channels": ["email", "push"],
            "reminderOffset": reminder_offset,
        },
    }

    dapr_url = f"http://localhost:{DAPR_HTTP_PORT}/v1.0/publish/{DAPR_PUBSUB_NAME}/reminders"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                dapr_url,
                json=event,
                headers={"Content-Type": "application/cloudevents+json"},
            )
            response.raise_for_status()

            # Track that we sent this reminder
            _sent_reminders[task_id] = datetime.now(timezone.utc)

            logger.info(
                f"Published reminder for task {task_id} "
                f"(due: {due_date.isoformat()}, user: {user_id})"
            )
            return True

    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error publishing reminder for task {task_id}",
            extra={"status_code": e.response.status_code},
        )
        return False
    except httpx.RequestError as e:
        logger.warning(
            f"Dapr not available for reminder publishing: {e}"
        )
        return False


def cleanup_tracking() -> int:
    """Remove old entries from the sent reminders tracking dict.

    Returns:
        Number of entries cleaned up.
    """
    now = datetime.now(timezone.utc)
    expired = [
        task_id
        for task_id, sent_time in _sent_reminders.items()
        if now - sent_time > _MAX_TRACKING_AGE
    ]
    for task_id in expired:
        del _sent_reminders[task_id]
    return len(expired)


async def scan_and_notify() -> dict:
    """Single scan cycle: fetch upcoming tasks and publish reminders.

    Returns:
        Summary of the scan cycle.
    """
    tasks = await fetch_upcoming_tasks(lookahead_minutes=60)
    sent_count = 0
    skipped_count = 0

    for task in tasks:
        task_id = str(task.get("id", ""))
        due_date_str = task.get("dueDate") or task.get("due_date")
        reminder_offset = task.get("reminderOffset") or task.get(
            "reminder_offset", DEFAULT_REMINDER_OFFSET_MINUTES
        )

        if not due_date_str:
            continue

        try:
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        if should_send_reminder(task_id, due_date, reminder_offset):
            success = await publish_reminder_event(task)
            if success:
                sent_count += 1
            else:
                skipped_count += 1
        else:
            skipped_count += 1

    # Periodic cleanup
    cleaned = cleanup_tracking()

    return {
        "tasks_scanned": len(tasks),
        "reminders_sent": sent_count,
        "skipped": skipped_count,
        "tracking_cleaned": cleaned,
    }


async def run_scheduler() -> None:
    """Run the reminder scheduler loop.

    Periodically scans for upcoming tasks and publishes reminder events.
    Designed to run as a background task during the service lifespan.
    """
    logger.info(
        f"Reminder scheduler starting "
        f"(interval={SCAN_INTERVAL_SECONDS}s, "
        f"default_offset={DEFAULT_REMINDER_OFFSET_MINUTES}min)"
    )

    while True:
        try:
            result = await scan_and_notify()
            logger.info(
                "Reminder scan complete",
                extra={
                    "tasks_scanned": result["tasks_scanned"],
                    "reminders_sent": result["reminders_sent"],
                },
            )
        except Exception as e:
            logger.exception(f"Error in reminder scan cycle: {e}")

        await asyncio.sleep(SCAN_INTERVAL_SECONDS)
