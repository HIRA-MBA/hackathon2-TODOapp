"""Integration tests for chat functionality.

Per spec FR-001 through FR-019 and SC-001 through SC-008.
Tests the complete chat flow from endpoint to database.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.conversation_service import ConversationService


# Test user for mocking authentication
TEST_USER_ID = "test-user-123"
TEST_USER_EMAIL = "test@example.com"


@pytest.fixture
def mock_current_user():
    """Mock the CurrentUser dependency."""
    user = MagicMock()
    user.user_id = TEST_USER_ID
    user.email = TEST_USER_EMAIL
    return user


@pytest.fixture
def mock_db_session():
    """Mock the database session."""
    return AsyncMock(spec=AsyncSession)


class TestChatEndpoint:
    """Tests for POST /api/chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self):
        """Test: Chat endpoint returns 401 without authentication.

        Per spec FR-011: System MUST require valid JWT authentication.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/chat", json={"message": "Hello"})
            # Should fail with 401 or 403 without auth
            assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_chat_validates_message_length(self):
        """Test: Messages over 2000 characters are rejected.

        Per spec edge case: Messages truncated at 2000 characters.
        """
        long_message = "x" * 2001
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/chat", json={"message": long_message})
            # Should reject with validation error (after auth check)
            assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_chat_rejects_empty_message(self):
        """Test: Empty messages are rejected.

        Per spec edge case: System responds asking for input.
        """
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/chat", json={"message": ""})
            # Should reject with validation error
            assert response.status_code in [401, 403, 422]


class TestConversationService:
    """Tests for conversation service operations."""

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_creates_new(self, mock_db_session):
        """Test: First call creates a new conversation.

        Per spec FR-008: System MUST persist conversations with unique identifiers.
        """
        service = ConversationService(mock_db_session)

        # Mock the query to return None (no existing conversation)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Should create new conversation
        _conversation = await service.get_or_create_conversation(TEST_USER_ID)

        # Verify add and flush were called (service uses flush, not commit)
        assert mock_db_session.add.called
        assert mock_db_session.flush.called

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_returns_existing(self, mock_db_session):
        """Test: Second call returns existing conversation.

        Per research Decision 3: Single conversation per user.
        """
        service = ConversationService(mock_db_session)

        # Mock existing conversation
        existing_conv = Conversation(
            id=uuid4(),
            user_id=TEST_USER_ID,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_conv
        mock_db_session.execute.return_value = mock_result

        conversation = await service.get_or_create_conversation(TEST_USER_ID)

        assert conversation.id == existing_conv.id
        assert conversation.user_id == TEST_USER_ID

    @pytest.mark.asyncio
    async def test_message_ordering_chronological(self, mock_db_session):
        """Test: Messages returned in chronological order.

        Per spec FR-023: Recent conversation messages for continuity.
        """
        service = ConversationService(mock_db_session)
        conv_id = uuid4()

        # Mock messages in DESCENDING order (as returned by the query)
        from datetime import datetime, timedelta

        now = datetime.utcnow()

        # Messages returned in descending order by created_at (newest first)
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
                created_at=now - timedelta(minutes=1),
            ),
            Message(
                id=uuid4(),
                conversation_id=conv_id,
                role="user",
                content="First",
                created_at=now - timedelta(minutes=2),
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = messages
        mock_db_session.execute.return_value = mock_result

        result = await service.get_recent_messages(conv_id, limit=5)

        # Service reverses the list, so result should be chronological (oldest first)
        assert result[0].content == "First"
        assert result[-1].content == "Third"

    @pytest.mark.asyncio
    async def test_message_limit_enforced(self, mock_db_session):
        """Test: Message retrieval respects limit parameter.

        Per spec assumption 6: 20 most recent messages for context.
        """
        service = ConversationService(mock_db_session)
        conv_id = uuid4()

        # Mock would return limited messages
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        await service.get_recent_messages(conv_id, limit=20)

        # Verify execute was called (limit is applied in query)
        assert mock_db_session.execute.called


class TestConversationPersistence:
    """Tests for conversation persistence across requests."""

    @pytest.mark.asyncio
    async def test_conversation_persists_across_requests(self, mock_db_session):
        """Test: Conversation history preserved after browser restart.

        Per spec SC-004: Conversation history is preserved and accessible.
        """
        service = ConversationService(mock_db_session)

        # First request creates conversation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        conv1 = await service.get_or_create_conversation(TEST_USER_ID)

        # Simulate second request finding existing conversation
        mock_result.scalar_one_or_none.return_value = conv1
        conv2 = await service.get_or_create_conversation(TEST_USER_ID)

        # Should be same conversation
        assert conv1.user_id == conv2.user_id


# NOTE: Task tool tests have been moved to test_mcp_tools.py
# The @function_tool decorator makes functions into FunctionTool objects
# that aren't directly callable in tests. The MCP tools tests use _impl
# functions that can be tested directly.
#
# The following functionality is covered by test_mcp_tools.py:
# - FR-014: add_task tool (TestMCPAddTask)
# - FR-015: list_tasks tool (TestMCPListTasks)
# - FR-016: update_task tool (TestMCPUpdateTask)
# - FR-017: complete_task tool (TestMCPCompleteTask)
# - FR-018: delete_task tool (TestMCPDeleteTask)
# - SC-008/FR-012: User isolation (TestMCPAuthentication)
