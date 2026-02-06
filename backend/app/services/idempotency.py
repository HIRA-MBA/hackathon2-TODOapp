"""Idempotent event processing utility.

Per data-model.md: Ensures at-least-once delivery becomes effectively
exactly-once by tracking processed events in the database.

Usage:
    async with idempotent_processor(event_id, consumer_id, session) as should_process:
        if should_process:
            await handle_event()
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processed_event import ProcessedEvent

logger = logging.getLogger(__name__)


class EventAlreadyProcessedError(Exception):
    """Raised when an event has already been processed."""

    def __init__(self, event_id: UUID, consumer_id: str):
        self.event_id = event_id
        self.consumer_id = consumer_id
        super().__init__(f"Event {event_id} already processed by {consumer_id}")


async def is_event_processed(
    session: AsyncSession,
    event_id: UUID,
    consumer_id: str,
) -> bool:
    """Check if an event has already been processed by this consumer."""
    result = await session.execute(
        select(ProcessedEvent).where(
            ProcessedEvent.event_id == event_id,
            ProcessedEvent.consumer_id == consumer_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def mark_event_processed(
    session: AsyncSession,
    event_id: UUID,
    consumer_id: str,
) -> ProcessedEvent:
    """Mark an event as processed by this consumer."""
    processed = ProcessedEvent(
        event_id=event_id,
        consumer_id=consumer_id,
        processed_at=datetime.utcnow(),
    )
    session.add(processed)
    await session.flush()
    return processed


@asynccontextmanager
async def idempotent_processor(
    event_id: UUID,
    consumer_id: str,
    session: AsyncSession,
    raise_on_duplicate: bool = False,
) -> AsyncGenerator[bool, None]:
    """Context manager for idempotent event processing.

    Per data-model.md pattern:
    1. Check if (event_id, consumer_id) exists
    2. If exists, skip processing (yield False or raise)
    3. If not, yield True and mark as processed after handler completes

    Args:
        event_id: CloudEvents ID
        consumer_id: Service identifier (e.g., 'recurring-task-service')
        session: Database session (should be within a transaction)
        raise_on_duplicate: If True, raise EventAlreadyProcessedError instead of yielding False

    Yields:
        True if event should be processed, False if already processed

    Example:
        async with idempotent_processor(event_id, "recurring-task-service", session) as should_process:
            if should_process:
                await create_next_task_instance(task)
    """
    # Check if already processed
    already_processed = await is_event_processed(session, event_id, consumer_id)

    if already_processed:
        logger.info(
            "event_already_processed",
            extra={
                "event_id": str(event_id),
                "consumer_id": consumer_id,
            },
        )
        if raise_on_duplicate:
            raise EventAlreadyProcessedError(event_id, consumer_id)
        yield False
        return

    # Not yet processed - yield control to handler
    try:
        yield True

        # Handler completed successfully - mark as processed
        await mark_event_processed(session, event_id, consumer_id)

        logger.info(
            "event_processed",
            extra={
                "event_id": str(event_id),
                "consumer_id": consumer_id,
            },
        )

    except Exception as e:
        # Handler failed - don't mark as processed (allow retry)
        logger.error(
            "event_processing_failed",
            extra={
                "event_id": str(event_id),
                "consumer_id": consumer_id,
                "error": str(e),
            },
        )
        raise


async def cleanup_old_events(
    session: AsyncSession,
    days_to_keep: int = 7,
) -> int:
    """Remove processed event records older than specified days.

    Returns the number of deleted records.
    """
    from datetime import timedelta
    from sqlalchemy import delete

    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

    result = await session.execute(
        delete(ProcessedEvent).where(ProcessedEvent.processed_at < cutoff)
    )
    await session.commit()

    deleted = result.rowcount
    logger.info(
        "processed_events_cleanup",
        extra={
            "deleted_count": deleted,
            "cutoff_date": cutoff.isoformat(),
        },
    )
    return deleted
