"""ProcessedEvent model for idempotent event processing.

Per data-model.md: Track processed events for deduplication (FR-015).
Uses composite primary key (event_id, consumer_id) to ensure each
event is processed exactly once per consumer service.
"""

from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class ProcessedEvent(SQLModel, table=True):
    """Tracks processed events for idempotency.

    Usage pattern:
    1. Before processing an event, check if (event_id, consumer_id) exists
    2. If exists, skip processing (already handled)
    3. If not, process event then insert record

    This ensures at-least-once delivery becomes effectively exactly-once.
    """

    __tablename__ = "processed_event"

    # Composite primary key
    event_id: UUID = Field(primary_key=True, description="CloudEvents ID")
    consumer_id: str = Field(
        primary_key=True,
        max_length=100,
        description="Service that processed the event (e.g., 'recurring-task-service')",
    )

    # When the event was processed
    processed_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,  # For cleanup queries
    )
