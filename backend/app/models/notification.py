"""NotificationPreference model for user notification settings.

Per data-model.md: User settings for notification delivery (FR-018).
"""

from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class NotificationPreference(SQLModel, table=True):
    """User notification preferences.

    Each user can have one preference record.
    If no record exists, defaults apply (email=True, push=True, offset=30).
    """

    __tablename__ = "notification_preference"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # User reference (unique - one preference per user)
    # Using str because Better Auth generates string IDs
    user_id: str = Field(max_length=64, unique=True, nullable=False, index=True)

    # Notification channels
    email_enabled: bool = Field(default=True)
    push_enabled: bool = Field(default=True)

    # Quiet hours (notifications deferred during this window)
    # Stored as string "HH:MM" for cross-timezone handling
    quiet_hours_start: Optional[str] = Field(default=None, max_length=5)
    quiet_hours_end: Optional[str] = Field(default=None, max_length=5)

    # User timezone for quiet hours calculation
    timezone: str = Field(default="UTC", max_length=64)

    # Default reminder offset in minutes before due_date
    default_reminder_offset: int = Field(default=30, ge=0)
