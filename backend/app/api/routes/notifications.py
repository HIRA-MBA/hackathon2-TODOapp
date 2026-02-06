"""Notification preferences API endpoints.

Per T079: API endpoints for managing user notification preferences.
Per api-extensions.yaml: CRUD operations for notification settings.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user_id
from app.dependencies.database import get_session
from app.services.notification_service import NotificationPreferenceService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationPreferenceCreate(BaseModel):
    """Request schema for creating/updating notification preferences."""
    email_enabled: bool = Field(True, alias="emailEnabled")
    push_enabled: bool = Field(True, alias="pushEnabled")
    quiet_hours_start: Optional[str] = Field(None, alias="quietHoursStart", description="HH:MM format")
    quiet_hours_end: Optional[str] = Field(None, alias="quietHoursEnd", description="HH:MM format")
    timezone: str = "UTC"

    class Config:
        populate_by_name = True


class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences."""
    id: UUID
    user_id: str = Field(alias="userId")
    email_enabled: bool = Field(alias="emailEnabled")
    push_enabled: bool = Field(alias="pushEnabled")
    quiet_hours_start: Optional[str] = Field(None, alias="quietHoursStart")
    quiet_hours_end: Optional[str] = Field(None, alias="quietHoursEnd")
    timezone: str

    class Config:
        populate_by_name = True
        from_attributes = True


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Get current user's notification preferences.

    Returns default preferences if not yet configured.
    """
    service = NotificationPreferenceService(session)
    prefs = await service.get_or_create_preferences(user_id)
    return prefs


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    data: NotificationPreferenceCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Update current user's notification preferences."""
    service = NotificationPreferenceService(session)
    prefs = await service.update_preferences(
        user_id=user_id,
        email_enabled=data.email_enabled,
        push_enabled=data.push_enabled,
        quiet_hours_start=data.quiet_hours_start,
        quiet_hours_end=data.quiet_hours_end,
        timezone=data.timezone,
    )
    return prefs


@router.delete("/preferences")
async def reset_preferences(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Reset notification preferences to defaults."""
    service = NotificationPreferenceService(session)
    await service.delete_preferences(user_id)
    return {"message": "Preferences reset to defaults"}
