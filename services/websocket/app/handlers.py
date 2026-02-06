"""Dapr Event Handlers for WebSocket Service.

Per T039: Handles task-updates events from Dapr pub/sub and broadcasts
to connected WebSocket clients.
"""

import logging
from datetime import datetime
from typing import Any

from app.connections import connection_manager
from app.filters import should_send_to_user

logger = logging.getLogger("websocket-service")


async def handle_task_update_event(event: dict[str, Any]) -> dict[str, str]:
    """Handle task update events from Dapr pub/sub.

    CloudEvents envelope structure:
    {
        "specversion": "1.0",
        "id": "event-uuid",
        "source": "https://api.todo.example.com/tasks",
        "type": "com.todo.task.created|updated|deleted|completed",
        "subject": "tasks/{task_id}",
        "time": "2026-02-04T12:00:00Z",
        "data": {
            "task_id": "uuid",
            "title": "...",
            "user_id": "...",
            ...
        }
    }

    Broadcasts to connected clients as:
    {
        "type": "task_update",
        "payload": {
            "action": "created|updated|deleted",
            "taskId": "uuid",
            "timestamp": "...",
            "task": { ... }
        }
    }
    """
    event_type = event.get("type", "")
    event_id = event.get("id", "unknown")
    data = event.get("data", {})

    # Extract user_id for routing
    user_id = data.get("user_id")
    if not user_id:
        logger.warning(
            "event_missing_user_id",
            extra={"event_id": event_id, "event_type": event_type},
        )
        return {"status": "SUCCESS"}  # ACK but don't broadcast

    # Map CloudEvents type to WebSocket action
    action_map = {
        "com.todo.task.created": "created",
        "com.todo.task.updated": "updated",
        "com.todo.task.deleted": "deleted",
        "com.todo.task.completed": "updated",  # Completed is a type of update
    }
    action = action_map.get(event_type, "updated")

    # Build WebSocket message
    task_snapshot = None
    if action != "deleted":
        task_snapshot = {
            "id": str(data.get("task_id")),
            "title": data.get("title"),
            "description": data.get("description"),
            "completed": data.get("completed", False),
            "priority": data.get("priority", "medium"),
            "dueDate": data.get("due_date"),
            "reminderOffset": data.get("reminder_offset", 30),
            "hasRecurrence": data.get("recurrence_id") is not None,
            "parentTaskId": str(data.get("parent_task_id")) if data.get("parent_task_id") else None,
            "createdAt": event.get("time"),
            "updatedAt": event.get("time"),
        }

    ws_message = {
        "type": "task_update",
        "payload": {
            "action": action,
            "taskId": str(data.get("task_id")),
            "timestamp": event.get("time", datetime.utcnow().isoformat()),
            "task": task_snapshot,
        },
    }

    # Broadcast to user's connections
    sent_count = await connection_manager.broadcast_to_user(user_id, ws_message)

    logger.info(
        "event_broadcast",
        extra={
            "event_id": event_id,
            "event_type": event_type,
            "user_id": user_id,
            "action": action,
            "sent_count": sent_count,
        },
    )

    return {"status": "SUCCESS"}


async def handle_connection_message(
    connection_id: str,
    message: dict[str, Any],
) -> dict[str, Any] | None:
    """Handle incoming WebSocket message from client.

    Returns response message or None if no response needed.
    """
    message_type = message.get("type", "")

    if message_type == "ping":
        # Update ping time and respond with pong
        connection_manager.update_ping(connection_id)
        return {
            "type": "pong",
            "payload": {
                "clientTimestamp": message.get("timestamp"),
                "serverTimestamp": int(datetime.utcnow().timestamp() * 1000),
            },
        }

    elif message_type == "subscribe":
        # Subscribe to updates
        scopes = message.get("payload", {}).get("scopes", ["own_tasks"])
        success = await connection_manager.subscribe(connection_id, scopes)

        if success:
            # Flush any missed events from reconnection
            flushed = await connection_manager.flush_missed_events(connection_id)
            if flushed > 0:
                logger.info(
                    "missed_events_flushed",
                    extra={"connection_id": connection_id, "count": flushed},
                )

        return {
            "type": "subscription_ack",
            "payload": {
                "scopes": scopes,
                "activeSubscriptions": 1 if success else 0,
            },
        }

    elif message_type == "unsubscribe":
        await connection_manager.unsubscribe(connection_id)
        logger.info("client_unsubscribed", extra={"connection_id": connection_id})
        return None  # No response needed

    else:
        logger.warning(
            "unknown_message_type",
            extra={"connection_id": connection_id, "type": message_type},
        )
        return {
            "type": "error",
            "payload": {
                "code": "INVALID_MESSAGE",
                "message": f"Unknown message type: {message_type}",
                "retryable": False,
            },
        }
