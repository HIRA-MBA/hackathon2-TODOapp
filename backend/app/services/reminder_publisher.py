"""Reminder Publisher Service.

Per T085: Publishes reminder events from the backend for tasks approaching
their due dates. Integrates with the EventPublisher to send reminder events
to the Dapr pub/sub reminders topic.

This service is called by the backend's task operations to schedule
reminders when tasks with due dates are created or updated.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.events import (
    ReminderEventType,
    ReminderEvent,
    ReminderEventData,
    create_reminder_event,
)
from app.services.event_publisher import get_event_publisher
from app.middleware.correlation import get_correlation_id

logger = logging.getLogger(__name__)

# Default reminder offset in minutes
DEFAULT_REMINDER_OFFSET = 30


class ReminderPublisher:
    """Publishes reminder events for tasks with upcoming due dates.

    Integrates with the Dapr EventPublisher to send reminder trigger
    events that the notification service consumes.
    """

    def __init__(self, default_offset_minutes: int = DEFAULT_REMINDER_OFFSET):
        self.default_offset = default_offset_minutes

    async def schedule_reminder(
        self,
        task_id: UUID,
        task_title: str,
        user_id: str,
        due_date: datetime,
        reminder_offset: int | None = None,
        channels: list[str] | None = None,
    ) -> bool:
        """Schedule a reminder for a task by publishing a reminder event.

        The notification service will receive this event and handle delivery
        at the appropriate time (due_date - offset).

        Args:
            task_id: The task to remind about.
            task_title: Task title for the notification message.
            user_id: Who to notify.
            due_date: When the task is due.
            reminder_offset: Minutes before due date to send reminder.
                Uses default if not specified.
            channels: Notification channels (email, push). Defaults to ["email"].

        Returns:
            True if the reminder event was published successfully.
        """
        offset = reminder_offset if reminder_offset is not None else self.default_offset
        scheduled_time = due_date - timedelta(minutes=offset)
        now = datetime.now(timezone.utc)

        # Don't schedule reminders for past times
        if scheduled_time <= now:
            logger.info(
                f"Skipping reminder for task {task_id}: "
                f"scheduled time {scheduled_time.isoformat()} is in the past"
            )
            return False

        # Don't schedule reminders for tasks due more than 7 days out
        if due_date - now > timedelta(days=7):
            logger.debug(
                f"Skipping reminder for task {task_id}: "
                f"due date {due_date.isoformat()} is more than 7 days away"
            )
            return False

        event = create_reminder_event(
            task_id=task_id,
            task_title=task_title,
            user_id=user_id,
            due_date=due_date,
            scheduled_time=scheduled_time,
            channels=channels or ["email"],
            correlation_id=get_correlation_id(),
        )

        publisher = get_event_publisher()
        success = await publisher.publish_reminder_event(
            event=event,
            correlation_id=get_correlation_id(),
        )

        if success:
            logger.info(
                "reminder_scheduled",
                extra={
                    "task_id": str(task_id),
                    "user_id": user_id,
                    "due_date": due_date.isoformat(),
                    "scheduled_time": scheduled_time.isoformat(),
                    "offset_minutes": offset,
                },
            )
        else:
            logger.warning(
                "reminder_schedule_failed",
                extra={
                    "task_id": str(task_id),
                    "user_id": user_id,
                },
            )

        return success

    async def cancel_reminder(
        self,
        task_id: UUID,
        user_id: str,
    ) -> bool:
        """Cancel a pending reminder by publishing a cancellation event.

        Args:
            task_id: The task whose reminder should be cancelled.
            user_id: The task owner.

        Returns:
            True if the cancellation event was published successfully.
        """
        event = ReminderEvent(
            type=ReminderEventType.CANCELLED,
            subject=f"reminders/{task_id}",
            correlationid=get_correlation_id(),
            data=ReminderEventData(
                task_id=task_id,
                task_title="",  # Not needed for cancellation
                user_id=user_id,
                due_date=datetime.now(timezone.utc),  # Placeholder
                scheduled_time=datetime.now(timezone.utc),
                channels=[],
            ),
        )

        publisher = get_event_publisher()
        success = await publisher.publish_reminder_event(event=event)

        if success:
            logger.info(
                "reminder_cancelled",
                extra={"task_id": str(task_id), "user_id": user_id},
            )

        return success

    async def reschedule_reminder(
        self,
        task_id: UUID,
        task_title: str,
        user_id: str,
        new_due_date: datetime,
        reminder_offset: int | None = None,
        channels: list[str] | None = None,
    ) -> bool:
        """Reschedule a reminder when a task's due date changes.

        Cancels the existing reminder and schedules a new one.

        Args:
            task_id: The task to reschedule.
            task_title: Task title for the notification.
            user_id: Who to notify.
            new_due_date: Updated due date.
            reminder_offset: Minutes before due date.
            channels: Notification channels.

        Returns:
            True if the new reminder was scheduled successfully.
        """
        # Cancel existing reminder
        await self.cancel_reminder(task_id, user_id)

        # Schedule new reminder
        return await self.schedule_reminder(
            task_id=task_id,
            task_title=task_title,
            user_id=user_id,
            due_date=new_due_date,
            reminder_offset=reminder_offset,
            channels=channels,
        )


# Global singleton
_reminder_publisher: ReminderPublisher | None = None


def get_reminder_publisher() -> ReminderPublisher:
    """Get the global reminder publisher instance."""
    global _reminder_publisher
    if _reminder_publisher is None:
        _reminder_publisher = ReminderPublisher()
    return _reminder_publisher
