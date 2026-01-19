from datetime import datetime
from uuid import UUID
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole


class ConversationService:
    """Service for conversation and message CRUD operations.

    Per spec FR-008: Persist all conversations with unique identifiers per user.
    Per spec FR-009: Persist all messages with timestamps and conversation references.
    Per spec FR-010: Stateless request handling - no in-memory session state.

    Per research Decision 3: Single conversation per user (MVP), database-backed
    session with per-request reconstruction.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(self, user_id: str) -> Conversation:
        """Get the user's conversation or create one if it doesn't exist.

        Per spec clarification: Single persistent conversation per user (never auto-expires).

        Args:
            user_id: The authenticated user's ID from JWT.

        Returns:
            The user's conversation (existing or newly created).
        """
        # Try to find existing conversation
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            return conversation

        # Create new conversation
        conversation = Conversation(user_id=user_id)
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_recent_messages(
        self, conversation_id: UUID, limit: int = 20
    ) -> list[Message]:
        """Get the most recent messages in a conversation.

        Per spec edge case: Only recent relevant messages are retrieved for context
        (last 20 messages).

        Per research Decision 2: 20 messages ≈ 2K tokens, leaving room for tool calls.

        Args:
            conversation_id: The conversation UUID.
            limit: Maximum number of messages to retrieve (default 20).

        Returns:
            Messages ordered by created_at ASC (oldest first for chat display).
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))

    async def create_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Create a new message in a conversation.

        Per spec FR-005: System MUST persist all assistant responses.
        Per spec FR-009: Persist all messages with timestamps.

        Args:
            conversation_id: The conversation UUID.
            role: The message role (user, assistant, or tool).
            content: The message content.
            metadata: Optional metadata (e.g., tool call details).

        Returns:
            The created message.
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def update_conversation_activity(self, conversation_id: UUID) -> None:
        """Update the last_activity_at timestamp for a conversation.

        Args:
            conversation_id: The conversation UUID.
        """
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(last_activity_at=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def clear_messages(self, conversation_id: UUID) -> int:
        """Delete all messages from a conversation.

        Per spec FR-029: System MUST provide a "Clear history" function that
        deletes all messages from the user's conversation while preserving
        the conversation container.

        Args:
            conversation_id: The conversation UUID.

        Returns:
            Number of messages deleted.
        """
        stmt = delete(Message).where(Message.conversation_id == conversation_id)
        result = await self.session.execute(stmt)
        return result.rowcount
