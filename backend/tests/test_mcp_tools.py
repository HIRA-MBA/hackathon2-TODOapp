"""Tests for MCP server tools.

Per unified dual-chat task management plan:
- Auth required (no fallback)
- Tool parity with task_tools.py
- Priority/due_date handling
- Cross-channel task visibility
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp.server import (
    get_user_id,
    current_user_id,
    # Import the _impl functions for direct testing
    _add_task_impl,
    _list_tasks_impl,
    _complete_task_impl,
    _delete_task_impl,
    _update_task_impl,
)


def create_mock_session_context():
    """Create a properly mocked async context manager for get_session."""
    mock_session = AsyncMock()

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    return mock_get_session, mock_session


# Test user for mocking authentication
TEST_USER_ID = "test-user-mcp-123"


@pytest.fixture
def mock_db_session():
    """Mock the database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def auth_context():
    """Set up authenticated user context."""
    token = current_user_id.set(TEST_USER_ID)
    yield TEST_USER_ID
    current_user_id.reset(token)


@pytest.fixture
def no_auth_context():
    """Set up unauthenticated context (no user)."""
    token = current_user_id.set(None)
    yield
    current_user_id.reset(token)


class TestMCPAuthentication:
    """Tests for MCP authentication requirements."""

    def test_get_user_id_requires_auth(self, no_auth_context):
        """Test: get_user_id raises ValueError without authentication.

        SECURITY: No fallback user - authentication is required.
        """
        with pytest.raises(ValueError, match="Authentication required"):
            get_user_id()

    def test_get_user_id_returns_authenticated_user(self, auth_context):
        """Test: get_user_id returns the authenticated user_id."""
        user_id = get_user_id()
        assert user_id == TEST_USER_ID

    @pytest.mark.asyncio
    async def test_add_task_requires_auth(self, no_auth_context):
        """Test: add_task returns error without authentication."""
        result = await _add_task_impl(title="Test task")
        assert "authentication required" in result

    @pytest.mark.asyncio
    async def test_list_tasks_requires_auth(self, no_auth_context):
        """Test: list_tasks returns error without authentication."""
        result = await _list_tasks_impl()
        assert "authentication required" in result

    @pytest.mark.asyncio
    async def test_complete_task_requires_auth(self, no_auth_context):
        """Test: complete_task returns error without authentication."""
        result = await _complete_task_impl(task_id=str(uuid4()))
        assert "authentication required" in result

    @pytest.mark.asyncio
    async def test_delete_task_requires_auth(self, no_auth_context):
        """Test: delete_task returns error without authentication."""
        result = await _delete_task_impl(task_id=str(uuid4()))
        assert "authentication required" in result

    @pytest.mark.asyncio
    async def test_update_task_requires_auth(self, no_auth_context):
        """Test: update_task returns error without authentication."""
        result = await _update_task_impl(task_id=str(uuid4()), title="New title")
        assert "authentication required" in result


class TestMCPAddTask:
    """Tests for MCP add_task tool with priority/due_date support."""

    @pytest.mark.asyncio
    async def test_add_task_basic(self, auth_context):
        """Test: add_task creates task with title only."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = uuid4()
                mock_task.title = "Buy groceries"
                mock_task.priority = "medium"
                mock_task.due_date = None
                # Use AsyncMock for async methods
                mock_service.create_task = AsyncMock(return_value=mock_task)

                result = await _add_task_impl(title="Buy groceries")

                assert "success" in result
                assert "Buy groceries" in result

    @pytest.mark.asyncio
    async def test_add_task_with_priority(self, auth_context):
        """Test: add_task accepts priority parameter."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = uuid4()
                mock_task.title = "Urgent task"
                mock_task.priority = "high"
                mock_task.due_date = None
                mock_service.create_task = AsyncMock(return_value=mock_task)

                result = await _add_task_impl(title="Urgent task", priority="high")

                assert "success" in result
                assert "priority: high" in result

    @pytest.mark.asyncio
    async def test_add_task_with_due_date(self, auth_context):
        """Test: add_task accepts due_date parameter."""
        due = datetime.now() + timedelta(days=7)

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = uuid4()
                mock_task.title = "Task with deadline"
                mock_task.priority = "medium"
                mock_task.due_date = due
                mock_service.create_task = AsyncMock(return_value=mock_task)

                result = await _add_task_impl(
                    title="Task with deadline", due_date=due.strftime("%Y-%m-%d")
                )

                assert "success" in result
                assert "due:" in result

    @pytest.mark.asyncio
    async def test_add_task_validates_priority(self, auth_context):
        """Test: add_task rejects invalid priority values."""
        result = await _add_task_impl(title="Test", priority="invalid")
        assert "error" in result
        assert "priority must be" in result

    @pytest.mark.asyncio
    async def test_add_task_validates_due_date_format(self, auth_context):
        """Test: add_task rejects invalid due_date format."""
        result = await _add_task_impl(title="Test", due_date="not-a-date")
        assert "error" in result
        assert "invalid due_date format" in result

    @pytest.mark.asyncio
    async def test_add_task_validates_title_required(self, auth_context):
        """Test: add_task requires non-empty title."""
        result = await _add_task_impl(title="")
        assert "error" in result
        assert "title cannot be empty" in result

    @pytest.mark.asyncio
    async def test_add_task_validates_title_length(self, auth_context):
        """Test: add_task rejects titles over 200 characters."""
        result = await _add_task_impl(title="x" * 201)
        assert "error" in result
        assert "200 characters" in result


class TestMCPListTasks:
    """Tests for MCP list_tasks tool with enhanced display."""

    @pytest.mark.asyncio
    async def test_list_tasks_shows_priority_indicators(self, auth_context):
        """Test: list_tasks shows priority indicators (!, -, .)."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.list_tasks = AsyncMock(
                    return_value=[
                        MagicMock(
                            id=uuid4(),
                            title="High priority",
                            completed=False,
                            priority="high",
                            due_date=None,
                        ),
                        MagicMock(
                            id=uuid4(),
                            title="Low priority",
                            completed=False,
                            priority="low",
                            due_date=None,
                        ),
                    ]
                )

                result = await _list_tasks_impl()

                assert "[!]" in result  # high priority
                assert "[.]" in result  # low priority

    @pytest.mark.asyncio
    async def test_list_tasks_shows_overdue_indicator(self, auth_context):
        """Test: list_tasks shows OVERDUE for past due dates."""
        yesterday = datetime.now() - timedelta(days=1)

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.list_tasks = AsyncMock(
                    return_value=[
                        MagicMock(
                            id=uuid4(),
                            title="Overdue task",
                            completed=False,
                            priority="medium",
                            due_date=yesterday,
                        ),
                    ]
                )

                result = await _list_tasks_impl()

                assert "OVERDUE" in result

    @pytest.mark.asyncio
    async def test_list_tasks_shows_today_indicator(self, auth_context):
        """Test: list_tasks shows TODAY for tasks due today."""
        today = datetime.now().replace(hour=23, minute=59)

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.list_tasks = AsyncMock(
                    return_value=[
                        MagicMock(
                            id=uuid4(),
                            title="Due today",
                            completed=False,
                            priority="medium",
                            due_date=today,
                        ),
                    ]
                )

                result = await _list_tasks_impl()

                assert "TODAY" in result

    @pytest.mark.asyncio
    async def test_list_tasks_filters_by_status(self, auth_context):
        """Test: list_tasks filters by pending/completed status."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.list_tasks = AsyncMock(
                    return_value=[
                        MagicMock(
                            id=uuid4(),
                            title="Pending task",
                            completed=False,
                            priority="medium",
                            due_date=None,
                        ),
                        MagicMock(
                            id=uuid4(),
                            title="Completed task",
                            completed=True,
                            priority="medium",
                            due_date=None,
                        ),
                    ]
                )

                # Filter pending only
                result = await _list_tasks_impl(status="pending")
                assert "Pending task" in result
                assert "Completed task" not in result

    @pytest.mark.asyncio
    async def test_list_tasks_searches_by_title(self, auth_context):
        """Test: list_tasks filters by search term."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.list_tasks = AsyncMock(
                    return_value=[
                        MagicMock(
                            id=uuid4(),
                            title="Buy groceries",
                            completed=False,
                            priority="medium",
                            due_date=None,
                        ),
                        MagicMock(
                            id=uuid4(),
                            title="Call mom",
                            completed=False,
                            priority="medium",
                            due_date=None,
                        ),
                    ]
                )

                result = await _list_tasks_impl(search="groceries")
                assert "Buy groceries" in result
                assert "Call mom" not in result

    @pytest.mark.asyncio
    async def test_list_tasks_uses_sort_by(self, auth_context):
        """Test: list_tasks passes sort_by parameter to service."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.list_tasks = AsyncMock(return_value=[])

                await _list_tasks_impl(sort_by="due_date")

                mock_service.list_tasks.assert_called_with(
                    TEST_USER_ID, sort_by="due_date"
                )


class TestMCPUpdateTask:
    """Tests for MCP update_task tool."""

    @pytest.mark.asyncio
    async def test_update_task_changes_title(self, auth_context):
        """Test: update_task can change task title."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = task_id
                mock_task.title = "New title"
                mock_service.get_task = AsyncMock(return_value=mock_task)
                mock_service.update_task = AsyncMock(return_value=mock_task)

                result = await _update_task_impl(
                    task_id=str(task_id), title="New title"
                )

                assert "success" in result
                assert "New title" in result

    @pytest.mark.asyncio
    async def test_update_task_changes_priority(self, auth_context):
        """Test: update_task can change task priority."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = task_id
                mock_task.title = "Task"
                mock_service.get_task = AsyncMock(return_value=mock_task)
                mock_service.update_task = AsyncMock(return_value=mock_task)

                result = await _update_task_impl(task_id=str(task_id), priority="high")

                assert "success" in result

    @pytest.mark.asyncio
    async def test_update_task_requires_field(self, auth_context):
        """Test: update_task requires at least one field to update."""
        result = await _update_task_impl(task_id=str(uuid4()))
        assert "error" in result
        assert "must provide at least one field" in result

    @pytest.mark.asyncio
    async def test_update_task_validates_priority(self, auth_context):
        """Test: update_task rejects invalid priority values."""
        result = await _update_task_impl(task_id=str(uuid4()), priority="invalid")
        assert "error" in result
        assert "priority must be" in result

    @pytest.mark.asyncio
    async def test_update_task_validates_task_id(self, auth_context):
        """Test: update_task rejects invalid task ID format."""
        result = await _update_task_impl(task_id="not-a-uuid", title="Test")
        assert "error" in result
        assert "invalid task ID format" in result

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, auth_context):
        """Test: update_task returns error for non-existent task."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.get_task = AsyncMock(return_value=None)

                result = await _update_task_impl(
                    task_id=str(task_id), title="New title"
                )

                assert "error" in result
                assert "not found" in result


class TestMCPCompleteTask:
    """Tests for MCP complete_task tool."""

    @pytest.mark.asyncio
    async def test_complete_task_marks_done(self, auth_context):
        """Test: complete_task marks task as completed."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                pending_task = MagicMock()
                pending_task.id = task_id
                pending_task.title = "Buy milk"
                pending_task.completed = False
                mock_service.get_task = AsyncMock(return_value=pending_task)

                completed_task = MagicMock()
                completed_task.title = "Buy milk"
                mock_service.toggle_task = AsyncMock(return_value=completed_task)

                result = await _complete_task_impl(task_id=str(task_id))

                assert "success" in result
                assert "done" in result

    @pytest.mark.asyncio
    async def test_complete_task_already_completed(self, auth_context):
        """Test: complete_task returns info for already completed task."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                completed_task = MagicMock()
                completed_task.id = task_id
                completed_task.title = "Already done"
                completed_task.completed = True
                mock_service.get_task = AsyncMock(return_value=completed_task)

                result = await _complete_task_impl(task_id=str(task_id))

                assert "info" in result
                assert "already completed" in result


class TestMCPDeleteTask:
    """Tests for MCP delete_task tool."""

    @pytest.mark.asyncio
    async def test_delete_task_removes_task(self, auth_context):
        """Test: delete_task removes the task."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = task_id
                mock_task.title = "Task to delete"
                mock_service.get_task = AsyncMock(return_value=mock_task)
                mock_service.delete_task = AsyncMock(return_value=True)

                result = await _delete_task_impl(task_id=str(task_id))

                assert "success" in result
                assert "deleted" in result

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, auth_context):
        """Test: delete_task returns error for non-existent task."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.get_task = AsyncMock(return_value=None)

                result = await _delete_task_impl(task_id=str(task_id))

                assert "error" in result
                assert "not found" in result


class TestMCPToolParity:
    """Tests to verify parity between MCP tools and task_tools.py."""

    def test_all_five_tools_exist(self):
        """Test: MCP server exposes all 5 required tools (via _impl functions)."""
        from app.mcp import server
        import asyncio

        # Verify all _impl functions are defined and are async
        assert hasattr(server, "_add_task_impl")
        assert hasattr(server, "_list_tasks_impl")
        assert hasattr(server, "_update_task_impl")
        assert hasattr(server, "_complete_task_impl")
        assert hasattr(server, "_delete_task_impl")

        # Verify they are async functions
        assert asyncio.iscoroutinefunction(server._add_task_impl)
        assert asyncio.iscoroutinefunction(server._list_tasks_impl)
        assert asyncio.iscoroutinefunction(server._update_task_impl)
        assert asyncio.iscoroutinefunction(server._complete_task_impl)
        assert asyncio.iscoroutinefunction(server._delete_task_impl)

    def test_add_task_has_priority_parameter(self):
        """Test: add_task supports priority parameter like task_tools.py."""
        import inspect

        sig = inspect.signature(_add_task_impl)
        params = list(sig.parameters.keys())

        assert "priority" in params
        assert sig.parameters["priority"].default == "medium"

    def test_add_task_has_due_date_parameter(self):
        """Test: add_task supports due_date parameter like task_tools.py."""
        import inspect

        sig = inspect.signature(_add_task_impl)
        params = list(sig.parameters.keys())

        assert "due_date" in params
        assert sig.parameters["due_date"].default is None

    def test_list_tasks_has_sort_by_parameter(self):
        """Test: list_tasks supports sort_by parameter like task_tools.py."""
        import inspect

        sig = inspect.signature(_list_tasks_impl)
        params = list(sig.parameters.keys())

        assert "sort_by" in params
        assert sig.parameters["sort_by"].default == "created_at"

    def test_list_tasks_has_search_parameter(self):
        """Test: list_tasks supports search parameter like task_tools.py."""
        import inspect

        sig = inspect.signature(_list_tasks_impl)
        params = list(sig.parameters.keys())

        assert "search" in params

    def test_update_task_has_all_parameters(self):
        """Test: update_task supports all update fields like task_tools.py."""
        import inspect

        sig = inspect.signature(_update_task_impl)
        params = list(sig.parameters.keys())

        assert "task_id" in params
        assert "title" in params
        assert "description" in params
        assert "priority" in params
        assert "due_date" in params
