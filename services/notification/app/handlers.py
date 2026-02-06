"""Event handlers for notification service.

Per T077-T083: Handles reminder events with:
- User notification preferences
- Quiet hours respect
- Multi-channel delivery simulation
- Reminder batching
"""

import logging
import os
from datetime import datetime, time
from typing import Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("notification-service")

# Backend API URL
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

# In-memory processed events set (for idempotency)
_processed_events: set[str] = set()


class NotificationPreference(BaseModel):
    """User notification preferences."""
    user_id: str = Field(alias="userId")
    email_enabled: bool = Field(True, alias="emailEnabled")
    push_enabled: bool = Field(True, alias="pushEnabled")
    quiet_hours_start: Optional[time] = Field(None, alias="quietHoursStart")
    quiet_hours_end: Optional[time] = Field(None, alias="quietHoursEnd")
    timezone: str = "UTC"

    class Config:
        populate_by_name = True


class ReminderData(BaseModel):
    """Reminder event data."""
    task_id: str = Field(alias="taskId")
    task_title: str = Field(alias="taskTitle")
    user_id: str = Field(alias="userId")
    due_date: datetime = Field(alias="dueDate")
    reminder_offset: int = Field(30, alias="reminderOffset")
    channels: list[str] = Field(default_factory=lambda: ["email", "push"])

    class Config:
        populate_by_name = True


class ReminderEvent(BaseModel):
    """CloudEvents envelope for reminder events."""
    id: str
    type: str
    source: str
    specversion: str = "1.0"
    time: Optional[datetime] = None
    data: dict

    def get_reminder_data(self) -> Optional[ReminderData]:
        """Extract reminder data from event."""
        try:
            return ReminderData.model_validate(self.data)
        except Exception as e:
            logger.error(f"Failed to parse reminder data: {e}")
            return None


# Default quiet hours (10 PM to 8 AM)
DEFAULT_QUIET_START = time(22, 0)
DEFAULT_QUIET_END = time(8, 0)

# Pending notifications for batching
_pending_notifications: dict[str, list[ReminderData]] = {}


async def is_event_processed(event_id: str) -> bool:
    """Check if event has already been processed (idempotency)."""
    return event_id in _processed_events


async def mark_event_processed(event_id: str) -> None:
    """Mark event as processed."""
    _processed_events.add(event_id)
    # Cleanup old events
    if len(_processed_events) > 10000:
        to_remove = list(_processed_events)[:5000]
        for item in to_remove:
            _processed_events.discard(item)


def is_quiet_hours(
    current_time: time,
    quiet_start: Optional[time] = None,
    quiet_end: Optional[time] = None,
) -> bool:
    """Check if current time is within quiet hours.

    Per T082: Respect quiet hours settings.

    Handles overnight quiet hours (e.g., 10 PM to 8 AM).
    """
    start = quiet_start or DEFAULT_QUIET_START
    end = quiet_end or DEFAULT_QUIET_END

    if start <= end:
        # Same day quiet hours (e.g., 1 PM to 3 PM)
        return start <= current_time <= end
    else:
        # Overnight quiet hours (e.g., 10 PM to 8 AM)
        return current_time >= start or current_time <= end


async def get_user_preferences(user_id: str) -> NotificationPreference:
    """Get user notification preferences from backend.

    Per T078: Fetch preferences for notification delivery decisions.

    Falls back to defaults if preferences not found.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BACKEND_URL}/api/notifications/preferences",
                headers={"X-User-Id": user_id},
            )

            if response.status_code == 200:
                return NotificationPreference.model_validate(response.json())

    except Exception as e:
        logger.warning(f"Could not fetch preferences for user {user_id}: {e}")

    # Return defaults
    return NotificationPreference(
        userId=user_id,
        emailEnabled=True,
        pushEnabled=True,
        quietHoursStart=None,
        quietHoursEnd=None,
        timezone="UTC",
    )


async def deliver_notification(
    reminder: ReminderData,
    preferences: NotificationPreference,
) -> dict:
    """Deliver notification via configured channels.

    Per T081: Simulate notification delivery (log email/push).

    In production, this would integrate with:
    - Email service (SendGrid, SES, etc.)
    - Push notification service (Firebase, APNs, etc.)
    """
    delivered_channels = []

    for channel in reminder.channels:
        if channel == "email" and preferences.email_enabled:
            # Simulate email delivery
            logger.info(
                f"📧 EMAIL: Reminder for '{reminder.task_title}' "
                f"(due: {reminder.due_date}) sent to user {reminder.user_id}"
            )
            delivered_channels.append("email")

        elif channel == "push" and preferences.push_enabled:
            # Simulate push notification
            logger.info(
                f"🔔 PUSH: Reminder for '{reminder.task_title}' "
                f"(due: {reminder.due_date}) sent to user {reminder.user_id}"
            )
            delivered_channels.append("push")

    return {
        "user_id": reminder.user_id,
        "task_id": reminder.task_id,
        "channels": delivered_channels,
    }


async def handle_reminder_trigger(event: ReminderEvent) -> dict:
    """Handle reminder trigger event and deliver notification.

    Per T077: Main handler for reminder events.

    Returns:
        Processing result with status and details
    """
    event_id = event.id
    logger.info(f"Processing reminder event: {event_id}")

    # Idempotency check
    if await is_event_processed(event_id):
        logger.info(f"Event {event_id} already processed, skipping")
        return {"status": "SKIPPED", "reason": "already_processed"}

    # Extract reminder data
    reminder = event.get_reminder_data()
    if not reminder:
        logger.error(f"Could not extract reminder data from event {event_id}")
        return {"status": "ERROR", "reason": "invalid_reminder_data"}

    # Get user preferences
    preferences = await get_user_preferences(reminder.user_id)

    # Check quiet hours
    current_time = datetime.utcnow().time()
    if is_quiet_hours(current_time, preferences.quiet_hours_start, preferences.quiet_hours_end):
        logger.info(
            f"Quiet hours active for user {reminder.user_id}, "
            f"deferring notification for task {reminder.task_id}"
        )
        # Add to pending for later delivery
        await queue_for_later(reminder)
        await mark_event_processed(event_id)
        return {"status": "DEFERRED", "reason": "quiet_hours"}

    # Deliver notification
    result = await deliver_notification(reminder, preferences)
    await mark_event_processed(event_id)

    logger.info(f"Notification delivered for event {event_id}: {result}")

    return {
        "status": "SUCCESS",
        "delivered": result,
    }


async def queue_for_later(reminder: ReminderData) -> None:
    """Queue notification for delivery after quiet hours.

    Per T083: Batch notifications for efficient delivery.
    """
    user_id = reminder.user_id
    if user_id not in _pending_notifications:
        _pending_notifications[user_id] = []

    _pending_notifications[user_id].append(reminder)
    logger.info(f"Queued reminder for user {user_id}, pending count: {len(_pending_notifications[user_id])}")


async def process_pending_notifications() -> dict:
    """Process pending notifications (called after quiet hours end).

    Per T083: Batch delivery of deferred notifications.

    This would typically be triggered by a scheduled job.
    """
    total_delivered = 0
    users_notified = 0

    for user_id, reminders in list(_pending_notifications.items()):
        if not reminders:
            continue

        preferences = await get_user_preferences(user_id)

        # Check if still in quiet hours
        current_time = datetime.utcnow().time()
        if is_quiet_hours(current_time, preferences.quiet_hours_start, preferences.quiet_hours_end):
            continue

        # Deliver batched notifications
        for reminder in reminders:
            await deliver_notification(reminder, preferences)
            total_delivered += 1

        users_notified += 1
        _pending_notifications[user_id] = []

    return {
        "users_notified": users_notified,
        "notifications_delivered": total_delivered,
    }
