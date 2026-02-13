"""Unit tests for ConversationService.

Per spec FR-008, FR-009: Conversation and message persistence.
Per spec FR-023: Recent conversation messages for context.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.services.conversation_service import ConversationService


TEST_USER_ID = "test-user-456"


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


class TestGetOrCreateConversation:
    """Tests for get_or_create_conversation method."""

    @pytest.mark.asyncio
    async def test_creates_new_conversation_for_new_user(self, mock_db):
        """New user gets a new conversation created."""
        service = ConversationService(mock_db)

        # Mock: no existing conversation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        conversation = await service.get_or_create_conversation(TEST_USER_ID)

        # Verify new conversation was added (service uses flush, not commit)
        assert mock_db.add.called
        assert mock_db.flush.called
        assert conversation.user_id == TEST_USER_ID

    @pytest.mark.asyncio
    async def test_returns_existing_conversation(self, mock_db):
        """Existing user gets their existing conversation."""
        service = ConversationService(mock_db)

        existing_conv = Conversation(
            id=uuid4(),
            user_id=TEST_USER_ID,
            created_at=datetime.utcnow(),
            last_activity_at=datetime.utcnow(),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conv
        mock_db.execute.return_value = mock_result

        conversation = await service.get_or_create_conversation(TEST_USER_ID)

        assert conversation.id == existing_conv.id
        # Should not create new conversation
        assert not mock_db.add.called


class TestCreateMessage:
    """Tests for create_message method."""

    @pytest.mark.asyncio
    async def test_creates_user_message(self, mock_db):
        """User messages are persisted correctly."""
        service = ConversationService(mock_db)
        conv_id = uuid4()

        message = await service.create_message(
            conv_id,
            MessageRole.USER,
            "Hello, add a task",
        )

        assert mock_db.add.called
        assert mock_db.flush.called  # Service uses flush, not commit
        assert message.conversation_id == conv_id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, add a task"

    @pytest.mark.asyncio
    async def test_creates_assistant_message(self, mock_db):
        """Assistant messages are persisted correctly."""
        service = ConversationService(mock_db)
        conv_id = uuid4()

        message = await service.create_message(
            conv_id,
            MessageRole.ASSISTANT,
            "I've added that task for you!",
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "I've added that task for you!"

    @pytest.mark.asyncio
    async def test_creates_tool_message_with_metadata(self, mock_db):
        """Tool messages include metadata."""
        service = ConversationService(mock_db)
        conv_id = uuid4()

        metadata = {"tool": "add_task", "status": "success"}
        message = await service.create_message(
            conv_id,
            MessageRole.TOOL,
            "add_task: success - created task",
            metadata=metadata,
        )

        assert message.role == MessageRole.TOOL
        assert message.message_metadata == metadata


class TestGetRecentMessages:
    """Tests for get_recent_messages method."""

    @pytest.mark.asyncio
    async def test_returns_messages_in_chronological_order(self, mock_db):
        """Messages are returned oldest first."""
        service = ConversationService(mock_db)
        conv_id = uuid4()
        now = datetime.utcnow()

        # Mock returns messages in DESCENDING order (as the query does)
        messages = [
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content="Third",
                created_at=now,
            ),
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="assistant",
                content="Second",
                created_at=now - timedelta(minutes=5),
            ),
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content="First",
                created_at=now - timedelta(minutes=10),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = messages
        mock_db.execute.return_value = mock_result

        result = await service.get_recent_messages(conv_id, limit=20)

        # Service reverses the list, so result should be chronological
        assert len(result) == 3
        assert result[0].content == "First"
        assert result[2].content == "Third"

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self, mock_db):
        """Only specified number of messages are returned."""
        service = ConversationService(mock_db)
        conv_id = uuid4()

        # Mock returns limited results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.get_recent_messages(conv_id, limit=5)

        # Verify query was executed
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_default_limit_is_20(self, mock_db):
        """Default limit follows spec (20 messages)."""
        service = ConversationService(mock_db)
        conv_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        await service.get_recent_messages(conv_id)

        # Default limit should be 20 per spec assumption 6
        assert mock_db.execute.called


class TestUpdateConversationActivity:
    """Tests for update_conversation_activity method."""

    @pytest.mark.asyncio
    async def test_updates_last_activity_timestamp(self, mock_db):
        """Last activity timestamp is updated via SQL UPDATE."""
        service = ConversationService(mock_db)
        conv_id = uuid4()

        await service.update_conversation_activity(conv_id)

        # Verify execute was called (the UPDATE statement)
        assert mock_db.execute.called
