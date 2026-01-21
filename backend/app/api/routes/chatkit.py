"""ChatKit session token API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.auth import CurrentUser
from app.services.chatkit_session_service import ChatkitSessionService

router = APIRouter(prefix="/chatkit", tags=["ChatKit"])


def get_chatkit_service(
    session: AsyncSession = Depends(get_session),
) -> ChatkitSessionService:
    """Dependency to get ChatkitSessionService instance."""
    return ChatkitSessionService(session)


ChatkitServiceDep = Annotated[ChatkitSessionService, Depends(get_chatkit_service)]


class TokenResponse(BaseModel):
    """Response model for session token creation."""

    token: str


@router.post("/token", response_model=TokenResponse)
async def create_session_token(
    user: CurrentUser,
    service: ChatkitServiceDep,
):
    """Create a new ChatKit session token for the authenticated user.

    This token can be used by the ChatKit workflow to authenticate
    MCP requests on behalf of the user.
    """
    token = await service.create_token(user.user_id)
    return TokenResponse(token=token)
