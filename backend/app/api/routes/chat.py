"""Chat API endpoints for AI chatbot.

Per spec FR-001: Single chat endpoint for natural language messages.
Per spec FR-011: Require valid JWT authentication.
Per spec FR-012: Scope all operations to authenticated user.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_session
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatStreamEvent,
    ConversationHistoryResponse,
    MessageResponse,
)
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Process a chat message and return streaming response.

    Per spec FR-001: Accept natural language messages from authenticated users.
    Per spec FR-011: JWT authentication required.

    Returns:
        SSE stream of ChatStreamEvent objects.
    """
    logger.info(f"Chat request from user {user.user_id}: {request.message[:50]}...")

    chat_service = ChatService(db)

    async def event_generator():
        """Generate SSE events from chat processing."""
        async for event in chat_service.process_message(
            user_id=user.user_id,
            email=user.email,
            message=request.message,
        ):
            yield {
                "event": event.type,
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(event_generator())


@router.get("/history")
async def get_history(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_session)],
    limit: int = 50,
) -> ConversationHistoryResponse:
    """Get the user's conversation history.

    Per spec FR-002: Load existing conversation from database.
    Per spec SC-004: Conversation history preserved and accessible.

    Args:
        limit: Maximum messages to retrieve (default 50, max 100).

    Returns:
        Conversation history with messages.
    """
    if limit > 100:
        limit = 100

    chat_service = ChatService(db)
    conversation_id, messages = await chat_service.get_conversation_history(
        user.user_id, limit=limit
    )

    if not conversation_id:
        return ConversationHistoryResponse(conversation_id="", messages=[])

    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=[
            MessageResponse(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                created_at=msg["created_at"],
            )
            for msg in messages
        ],
    )
