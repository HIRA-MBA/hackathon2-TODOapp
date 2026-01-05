"""Create task table

Revision ID: 001
Revises:
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for filtering tasks by user
    op.create_index("idx_task_user_id", "task", ["user_id"])
    # Composite index for ordered task listing by user
    op.create_index(
        "idx_task_user_created", "task", ["user_id", sa.text("created_at DESC")]
    )


def downgrade() -> None:
    op.drop_index("idx_task_user_created", table_name="task")
    op.drop_index("idx_task_user_id", table_name="task")
    op.drop_table("task")
