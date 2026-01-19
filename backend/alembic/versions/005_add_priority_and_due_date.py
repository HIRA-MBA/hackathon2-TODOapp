"""Add priority and due_date columns to task table

Revision ID: 005
Revises: 004
Create Date: 2026-01-18

Add priority (high/medium/low) and due_date fields to tasks.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "task",
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="medium"),
    )
    op.add_column(
        "task",
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
    )
    # Index for efficient due date queries
    op.create_index("idx_task_due_date", "task", ["due_date"])


def downgrade() -> None:
    op.drop_index("idx_task_due_date", table_name="task")
    op.drop_column("task", "due_date")
    op.drop_column("task", "priority")
