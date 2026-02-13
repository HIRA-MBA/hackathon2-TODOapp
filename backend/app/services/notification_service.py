"""Notification preference service.

Per T078: Service for managing user notification preferences.
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationPreference


class NotificationPreferenceService:
    """Service for notification preference CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get notification preferences for a user."""
        result = await self.session.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_preferences(self, user_id: str) -> NotificationPreference:
        """Get existing preferences or create defaults."""
        prefs = await self.get_preferences(user_id)

        if prefs is None:
            prefs = NotificationPreference(
                id=uuid4(),
                user_id=user_id,
                email_enabled=True,
                push_enabled=True,
                quiet_hours_start=None,
                quiet_hours_end=None,
                timezone="UTC",
            )
            self.session.add(prefs)
            await self.session.commit()
            await self.session.refresh(prefs)

        return prefs

    async def update_preferences(
        self,
        user_id: str,
        email_enabled: bool = True,
        push_enabled: bool = True,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None,
        timezone: str = "UTC",
    ) -> NotificationPreference:
        """Update or create notification preferences."""
        prefs = await self.get_preferences(user_id)

        if prefs is None:
            prefs = NotificationPreference(
                id=uuid4(),
                user_id=user_id,
            )
            self.session.add(prefs)

        prefs.email_enabled = email_enabled
        prefs.push_enabled = push_enabled
        prefs.quiet_hours_start = quiet_hours_start
        prefs.quiet_hours_end = quiet_hours_end
        prefs.timezone = timezone

        await self.session.commit()
        await self.session.refresh(prefs)

        return prefs

    async def delete_preferences(self, user_id: str) -> bool:
        """Delete user's notification preferences (reset to defaults)."""
        prefs = await self.get_preferences(user_id)

        if prefs:
            await self.session.delete(prefs)
            await self.session.commit()
            return True

        return False
