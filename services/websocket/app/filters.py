"""User-scoped message filtering for WebSocket broadcasts.

Per T040: Implements filtering logic to ensure users only receive
updates they're authorized to see.
"""

import logging
from typing import Any

logger = logging.getLogger("websocket-service")


def should_send_to_user(
    event_user_id: str,
    connection_user_id: str,
    scopes: list[str],
    event_data: dict[str, Any] | None = None,
) -> bool:
    """Determine if an event should be sent to a specific user connection.

    Filtering rules based on subscription scopes:
    - own_tasks: Only receive updates for tasks owned by the user
    - shared_tasks: Receive updates for tasks shared with the user (future feature)
    - all: Receive all updates (admin only, future feature)

    Args:
        event_user_id: User ID from the event (task owner)
        connection_user_id: User ID of the WebSocket connection
        scopes: List of subscribed scopes for this connection
        event_data: Optional event data for advanced filtering

    Returns:
        True if the event should be sent to this connection
    """
    # Default scope is own_tasks
    if not scopes:
        scopes = ["own_tasks"]

    # Check each scope
    for scope in scopes:
        if scope == "own_tasks":
            # User only sees their own tasks
            if event_user_id == connection_user_id:
                return True

        elif scope == "shared_tasks":
            # Future: Check if task is shared with this user
            # For now, shared_tasks includes own tasks
            if event_user_id == connection_user_id:
                return True
            # TODO: Check sharing permissions when implemented

        elif scope == "all":
            # Admin scope - see everything
            # Future: Verify user has admin role
            # For now, this is disabled for security
            logger.warning(
                "all_scope_requested",
                extra={
                    "connection_user_id": connection_user_id,
                    "event_user_id": event_user_id,
                },
            )
            # Only allow if it's their own task (security fallback)
            if event_user_id == connection_user_id:
                return True

    return False


def filter_task_data(
    task_data: dict[str, Any],
    connection_user_id: str,
    scopes: list[str],
) -> dict[str, Any] | None:
    """Filter task data before sending to client.

    Removes sensitive fields that the user shouldn't see.
    Returns None if the entire task should be filtered out.

    Args:
        task_data: Task snapshot from event
        connection_user_id: User ID of the WebSocket connection
        scopes: Subscription scopes

    Returns:
        Filtered task data or None if should not be sent
    """
    if not task_data:
        return None

    # For own_tasks, no filtering needed - user sees all their data
    if "own_tasks" in scopes:
        return task_data

    # For shared_tasks, might need to filter sensitive fields
    # Future: Implement field-level filtering for shared tasks

    return task_data


def get_allowed_scopes(user_id: str, requested_scopes: list[str]) -> list[str]:
    """Validate and filter requested scopes based on user permissions.

    Args:
        user_id: The requesting user's ID
        requested_scopes: Scopes the client wants to subscribe to

    Returns:
        List of actually allowed scopes
    """
    # For now, only own_tasks is fully supported
    allowed = []

    for scope in requested_scopes:
        if scope == "own_tasks":
            allowed.append(scope)
        elif scope == "shared_tasks":
            # Allow but functionality is limited
            allowed.append(scope)
        elif scope == "all":
            # Disabled for security - downgrade to own_tasks
            logger.warning(
                "scope_downgraded",
                extra={"user_id": user_id, "requested": scope, "granted": "own_tasks"},
            )
            if "own_tasks" not in allowed:
                allowed.append("own_tasks")

    # Default to own_tasks if nothing allowed
    if not allowed:
        allowed = ["own_tasks"]

    return allowed
