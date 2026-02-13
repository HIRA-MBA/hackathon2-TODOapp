"""Tests for MCP server tools.

Tests the actual @mcp.tool decorated functions from server.py.
Authentication, validation, CRUD operations, and tool parity.
"""

import pytest
import asyncio
import inspect
from uuid import uuid4
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch, MagicMock

from app.mcp.server import (
    get_user_id,
    current_user_id,
    add_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task,
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
    from sqlalchemy.ext.asyncio import AsyncSession

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
        result = await add_task.fn(title="Test task")
        assert "not authenticated" in result.lower()

    @pytest.mark.asyncio
    async def test_list_tasks_requires_auth(self, no_auth_context):
        """Test: list_tasks returns error without authentication."""
        result = await list_tasks.fn()
        assert "not authenticated" in result.lower()

    @pytest.mark.asyncio
    async def test_complete_task_requires_auth(self, no_auth_context):
        """Test: complete_task returns error without authentication."""
        result = await complete_task.fn(task_id=str(uuid4()))
        assert "not authenticated" in result.lower()

    @pytest.mark.asyncio
    async def test_delete_task_requires_auth(self, no_auth_context):
        """Test: delete_task returns error without authentication."""
        result = await delete_task.fn(task_id=str(uuid4()))
        assert "not authenticated" in result.lower()

    @pytest.mark.asyncio
    async def test_update_task_requires_auth(self, no_auth_context):
        """Test: update_task returns error without authentication."""
        result = await update_task.fn(task_id=str(uuid4()), title="New title")
        assert "not authenticated" in result.lower()


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
                mock_service.create_task = AsyncMock(return_value=mock_task)

                result = await add_task.fn(title="Buy groceries")

                assert "Created task" in result
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

                result = await add_task.fn(title="Urgent task", priority="high")

                assert "Created task" in result
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

                result = await add_task.fn(
                    title="Task with deadline", due_date=due.strftime("%Y-%m-%d")
                )

                assert "Created task" in result
                assert "due:" in result

    @pytest.mark.asyncio
    async def test_add_task_invalid_priority_defaults_to_medium(self, auth_context):
        """Test: add_task defaults invalid priority to medium."""
        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_task = MagicMock()
                mock_task.id = uuid4()
                mock_task.title = "Test"
                mock_task.priority = "medium"
                mock_task.due_date = None
                mock_service.create_task = AsyncMock(return_value=mock_task)

                result = await add_task.fn(title="Test", priority="invalid")

                # Should succeed with defaulted priority
                assert "Created task" in result
                assert "Test" in result

    @pytest.mark.asyncio
    async def test_add_task_validates_due_date_format(self, auth_context):
        """Test: add_task rejects invalid due_date format."""
        result = await add_task.fn(title="Test", due_date="not-a-date")
        assert "error" in result.lower()
        assert "invalid date format" in result.lower()

    @pytest.mark.asyncio
    async def test_add_task_validates_title_required(self, auth_context):
        """Test: add_task requires non-empty title."""
        result = await add_task.fn(title="")
        assert "error" in result.lower()
        assert "title cannot be empty" in result.lower()

    @pytest.mark.asyncio
    async def test_add_task_validates_title_length(self, auth_context):
        """Test: add_task rejects titles over 200 characters."""
        result = await add_task.fn(title="x" * 201)
        assert "error" in result.lower()
        assert "200 characters" in result.lower()


class TestMCPListTasks:
    """Tests for MCP list_tasks tool with enhanced display."""

    @pytest.mark.asyncio
    async def test_list_tasks_shows_priority_indicators(self, auth_context):
        """Test: list_tasks shows priority indicators (!, .)."""
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

                result = await list_tasks.fn()

                # Format: {priority_marker}[{status}] {title}
                # high="!", low="."
                assert "![TODO]" in result  # high priority marker before status
                assert ".[TODO]" in result  # low priority marker before status

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

                result = await list_tasks.fn()

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

                result = await list_tasks.fn()

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
                result = await list_tasks.fn(filter_status="pending")
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

                result = await list_tasks.fn(search="groceries")
                assert "Buy groceries" in result
                assert "Call mom" not in result


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

                result = await update_task.fn(task_id=str(task_id), title="New title")

                assert "Updated" in result
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

                result = await update_task.fn(task_id=str(task_id), priority="high")

                assert "Updated" in result

    @pytest.mark.asyncio
    async def test_update_task_requires_field(self, auth_context):
        """Test: update_task requires at least one field to update."""
        result = await update_task.fn(task_id=str(uuid4()))
        assert "error" in result.lower()
        assert "at least one field" in result.lower()

    @pytest.mark.asyncio
    async def test_update_task_validates_priority(self, auth_context):
        """Test: update_task rejects invalid priority values."""
        result = await update_task.fn(task_id=str(uuid4()), priority="invalid")
        assert "error" in result.lower()
        assert "priority must be" in result.lower()

    @pytest.mark.asyncio
    async def test_update_task_validates_task_id(self, auth_context):
        """Test: update_task rejects invalid task ID format."""
        result = await update_task.fn(task_id="not-a-uuid", title="Test")
        assert "error" in result.lower()
        assert "invalid task id" in result.lower()

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, auth_context):
        """Test: update_task returns error for non-existent task."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.get_task = AsyncMock(return_value=None)

                result = await update_task.fn(task_id=str(task_id), title="New title")

                assert "error" in result.lower()
                assert "not found" in result.lower()


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

                result = await complete_task.fn(task_id=str(task_id))

                assert "Completed" in result
                assert "Buy milk" in result

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

                result = await complete_task.fn(task_id=str(task_id))

                assert "already completed" in result.lower()


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

                result = await delete_task.fn(task_id=str(task_id))

                assert "Deleted" in result
                assert "Task to delete" in result

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, auth_context):
        """Test: delete_task returns error for non-existent task."""
        task_id = uuid4()

        mock_get_session, mock_session = create_mock_session_context()

        with patch("app.mcp.server.get_session", mock_get_session):
            with patch("app.mcp.server.TaskService") as MockTaskService:
                mock_service = MockTaskService.return_value
                mock_service.get_task = AsyncMock(return_value=None)

                result = await delete_task.fn(task_id=str(task_id))

                assert "error" in result.lower()
                assert "not found" in result.lower()


class TestMCPToolParity:
    """Tests to verify MCP tool signatures and availability."""

    def test_all_five_tools_exist(self):
        """Test: MCP server exposes all 5 required tools."""
        from app.mcp import server

        assert hasattr(server, "add_task")
        assert hasattr(server, "list_tasks")
        assert hasattr(server, "update_task")
        assert hasattr(server, "complete_task")
        assert hasattr(server, "delete_task")

        # Verify the underlying functions are async
        assert asyncio.iscoroutinefunction(server.add_task.fn)
        assert asyncio.iscoroutinefunction(server.list_tasks.fn)
        assert asyncio.iscoroutinefunction(server.update_task.fn)
        assert asyncio.iscoroutinefunction(server.complete_task.fn)
        assert asyncio.iscoroutinefunction(server.delete_task.fn)

    def test_add_task_has_priority_parameter(self):
        """Test: add_task supports priority parameter."""
        sig = inspect.signature(add_task.fn)
        params = list(sig.parameters.keys())

        assert "priority" in params
        assert sig.parameters["priority"].default == "medium"

    def test_add_task_has_due_date_parameter(self):
        """Test: add_task supports due_date parameter."""
        sig = inspect.signature(add_task.fn)
        params = list(sig.parameters.keys())

        assert "due_date" in params
        assert sig.parameters["due_date"].default == ""

    def test_list_tasks_has_filter_status_parameter(self):
        """Test: list_tasks supports filter_status parameter."""
        sig = inspect.signature(list_tasks.fn)
        params = list(sig.parameters.keys())

        assert "filter_status" in params
        assert sig.parameters["filter_status"].default == "all"

    def test_list_tasks_has_search_parameter(self):
        """Test: list_tasks supports search parameter."""
        sig = inspect.signature(list_tasks.fn)
        params = list(sig.parameters.keys())

        assert "search" in params

    def test_update_task_has_all_parameters(self):
        """Test: update_task supports all update fields."""
        sig = inspect.signature(update_task.fn)
        params = list(sig.parameters.keys())

        assert "task_id" in params
        assert "title" in params
        assert "description" in params
        assert "priority" in params
        assert "due_date" in params
