"""Dapr Event Publisher Service.

Per plan.md and data-model.md: Implements event publishing to Redpanda
via Dapr pub/sub with at-least-once delivery guarantee.

Topics:
- task-events: Task CRUD operations (consumed by recurring-task, notification, websocket)
- task-updates: Real-time sync (consumed by websocket service)
- reminders: Scheduled notifications (consumed by notification service)
"""

import logging
import os
from typing import Any

import httpx

from app.models.events import TaskEvent, ReminderEvent

logger = logging.getLogger(__name__)

# Dapr sidecar configuration
DAPR_HTTP_PORT = os.environ.get("DAPR_HTTP_PORT", "3500")
DAPR_PUBSUB_NAME = os.environ.get("DAPR_PUBSUB_NAME", "pubsub")
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}"

# Topic names per data-model.md
TOPIC_TASK_EVENTS = "task-events"
TOPIC_TASK_UPDATES = "task-updates"
TOPIC_REMINDERS = "reminders"


class EventPublisher:
    """Publishes events to Dapr pub/sub topics.

    Features:
    - At-least-once delivery via Dapr
    - Retry with exponential backoff on failures
    - Correlation ID propagation for distributed tracing
    - Fallback queue for offline mode (local dev without Dapr)
    """

    def __init__(
        self,
        dapr_url: str = DAPR_BASE_URL,
        pubsub_name: str = DAPR_PUBSUB_NAME,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        self.dapr_url = dapr_url
        self.pubsub_name = pubsub_name
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._fallback_queue: list[dict[str, Any]] = []

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _publish_to_dapr(
        self,
        topic: str,
        data: dict[str, Any],
        metadata: dict[str, str] | None = None,
    ) -> bool:
        """Publish event to Dapr pub/sub.

        Returns True if successful, False if failed.
        """
        url = f"{self.dapr_url}/v1.0/publish/{self.pubsub_name}/{topic}"

        headers = {
            "Content-Type": "application/cloudevents+json",
        }
        if metadata:
            # Dapr metadata headers (e.g., partition key)
            for key, value in metadata.items():
                headers[f"metadata.{key}"] = value

        client = await self._get_client()

        for attempt in range(self.max_retries):
            try:
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()

                logger.info(
                    "event_published",
                    extra={
                        "topic": topic,
                        "event_id": data.get("id"),
                        "event_type": data.get("type"),
                    },
                )
                return True

            except httpx.HTTPStatusError as e:
                logger.warning(
                    "event_publish_http_error",
                    extra={
                        "topic": topic,
                        "event_id": data.get("id"),
                        "status_code": e.response.status_code,
                        "attempt": attempt + 1,
                    },
                )
            except httpx.RequestError as e:
                logger.warning(
                    "event_publish_request_error",
                    extra={
                        "topic": topic,
                        "event_id": data.get("id"),
                        "error": str(e),
                        "attempt": attempt + 1,
                    },
                )

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                import asyncio

                await asyncio.sleep(2**attempt)

        # All retries failed - add to fallback queue
        logger.error(
            "event_publish_failed",
            extra={
                "topic": topic,
                "event_id": data.get("id"),
                "max_retries": self.max_retries,
            },
        )
        self._fallback_queue.append(
            {"topic": topic, "data": data, "metadata": metadata}
        )
        return False

    async def publish_task_event(
        self,
        event: TaskEvent,
        correlation_id: str | None = None,
    ) -> bool:
        """Publish a task event to the task-events topic.

        Also publishes to task-updates for real-time sync.
        """
        # Override correlation ID if provided
        if correlation_id:
            event.correlationid = correlation_id

        event_data = event.model_dump(mode="json")

        # Partition by user_id for ordering guarantees
        user_id = event.data.user_id
        metadata = {"partitionKey": user_id}

        # Publish to task-events (for recurring-task, notification services)
        success = await self._publish_to_dapr(TOPIC_TASK_EVENTS, event_data, metadata)

        # Also publish to task-updates (for websocket real-time sync)
        await self._publish_to_dapr(TOPIC_TASK_UPDATES, event_data, metadata)

        return success

    async def publish_reminder_event(
        self,
        event: ReminderEvent,
        correlation_id: str | None = None,
    ) -> bool:
        """Publish a reminder event to the reminders topic."""
        if correlation_id:
            event.correlationid = correlation_id

        event_data = event.model_dump(mode="json")

        # Partition by user_id
        user_id = event.data.user_id
        metadata = {"partitionKey": user_id}

        return await self._publish_to_dapr(TOPIC_REMINDERS, event_data, metadata)

    async def publish_raw(
        self,
        topic: str,
        data: dict[str, Any],
        partition_key: str | None = None,
    ) -> bool:
        """Publish raw data to a topic (for advanced use cases)."""
        metadata = {"partitionKey": partition_key} if partition_key else None
        return await self._publish_to_dapr(topic, data, metadata)

    def get_fallback_queue(self) -> list[dict[str, Any]]:
        """Get events that failed to publish (for retry or inspection)."""
        return list(self._fallback_queue)

    def clear_fallback_queue(self) -> None:
        """Clear the fallback queue."""
        self._fallback_queue.clear()

    async def retry_fallback_queue(self) -> int:
        """Retry publishing events from the fallback queue.

        Returns the number of successfully published events.
        """
        if not self._fallback_queue:
            return 0

        successful = 0
        remaining = []

        for item in self._fallback_queue:
            success = await self._publish_to_dapr(
                item["topic"],
                item["data"],
                item.get("metadata"),
            )
            if success:
                successful += 1
            else:
                remaining.append(item)

        self._fallback_queue = remaining
        return successful


# Global singleton instance
_event_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher


async def shutdown_event_publisher() -> None:
    """Shutdown the global event publisher."""
    global _event_publisher
    if _event_publisher:
        await _event_publisher.close()
        _event_publisher = None
