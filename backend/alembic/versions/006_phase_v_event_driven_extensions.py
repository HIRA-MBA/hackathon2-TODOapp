"""Phase V: Event-Driven Extensions

Revision ID: 006
Revises: 2622ddabaf3c
Create Date: 2026-02-04

Per data-model.md Migration Strategy:
1. Create recurrence_pattern table (referenced by tasks)
2. Add recurrence columns to task table
3. Create notification_preference table
4. Create processed_event table (idempotency tracking)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "2622ddabaf3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create recurrence_pattern table
    op.create_table(
        "recurrence_pattern",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "frequency",
            sa.String(20),
            nullable=False,
        ),
        sa.Column("interval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("by_weekday", ARRAY(sa.Integer()), nullable=True),
        sa.Column("by_monthday", sa.Integer(), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_occurrences", sa.Integer(), nullable=True),
        sa.Column("rrule_string", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        # Constraint: Either end_date OR max_occurrences must be set (not both, not neither)
        sa.CheckConstraint(
            "(end_date IS NOT NULL AND max_occurrences IS NULL) OR "
            "(end_date IS NULL AND max_occurrences IS NOT NULL)",
            name="recurrence_end_condition_check",
        ),
        sa.CheckConstraint("interval >= 1", name="recurrence_interval_check"),
        sa.CheckConstraint(
            "by_monthday IS NULL OR (by_monthday >= 1 AND by_monthday <= 31)",
            name="recurrence_monthday_check",
        ),
    )

    # 2. Add recurrence columns to task table
    op.add_column(
        "task",
        sa.Column(
            "recurrence_id",
            sa.UUID(),
            sa.ForeignKey("recurrence_pattern.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "task",
        sa.Column(
            "parent_task_id",
            sa.UUID(),
            sa.ForeignKey("task.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "task",
        sa.Column("reminder_offset", sa.Integer(), nullable=False, server_default="30"),
    )

    # Index for parent task lookups (recurring instances)
    op.create_index(
        "idx_task_parent",
        "task",
        ["parent_task_id"],
        postgresql_where=sa.text("parent_task_id IS NOT NULL"),
    )
    op.create_index("idx_task_recurrence", "task", ["recurrence_id"])

    # 3. Create notification_preference table
    op.create_table(
        "notification_preference",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(64), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
        sa.Column(
            "default_reminder_offset", sa.Integer(), nullable=False, server_default="30"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_notification_preference_user"),
    )
    op.create_index(
        "idx_notification_preference_user", "notification_preference", ["user_id"]
    )

    # 4. Create processed_event table (idempotency)
    op.create_table(
        "processed_event",
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("consumer_id", sa.String(100), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("event_id", "consumer_id"),
    )
    op.create_index(
        "idx_processed_event_time", "processed_event", ["processed_at"]
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_index("idx_processed_event_time", table_name="processed_event")
    op.drop_table("processed_event")

    op.drop_index("idx_notification_preference_user", table_name="notification_preference")
    op.drop_table("notification_preference")

    op.drop_index("idx_task_recurrence", table_name="task")
    op.drop_index("idx_task_parent", table_name="task")
    op.drop_column("task", "reminder_offset")
    op.drop_column("task", "parent_task_id")
    op.drop_column("task", "recurrence_id")

    op.drop_table("recurrence_pattern")
