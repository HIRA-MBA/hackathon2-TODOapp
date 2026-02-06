# Models package
from app.models.task import Task, Priority
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.chatkit_session import ChatkitSession

# Phase V: Event-driven models
from app.models.recurrence import RecurrencePattern, RecurrenceFrequency
from app.models.notification import NotificationPreference
from app.models.processed_event import ProcessedEvent
from app.models.events import (
    TaskEvent,
    TaskEventData,
    TaskEventType,
    ReminderEvent,
    ReminderEventData,
    ReminderEventType,
    create_task_event,
    create_reminder_event,
)

__all__ = [
    # Core models
    "Task",
    "Priority",
    "Conversation",
    "Message",
    "MessageRole",
    "ChatkitSession",
    # Phase V models
    "RecurrencePattern",
    "RecurrenceFrequency",
    "NotificationPreference",
    "ProcessedEvent",
    # Event models
    "TaskEvent",
    "TaskEventData",
    "TaskEventType",
    "ReminderEvent",
    "ReminderEventData",
    "ReminderEventType",
    "create_task_event",
    "create_reminder_event",
]
