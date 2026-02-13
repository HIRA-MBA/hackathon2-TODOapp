"""Change user_id from UUID to VARCHAR(64) for Better Auth compatibility

Better Auth generates non-UUID string IDs like '7OMgLqJ4nHFamYC3ojPQLGv0yBoUmBrS'.

Revision ID: 002
Revises: 001
Create Date: 2026-01-03

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing indexes that depend on user_id
    op.drop_index("idx_task_user_created", table_name="task")
    op.drop_index("idx_task_user_id", table_name="task")

    # Change user_id column from UUID to VARCHAR(64)
    op.alter_column(
        "task",
        "user_id",
        existing_type=sa.Uuid(),
        type_=sa.String(length=64),
        existing_nullable=False,
        postgresql_using="user_id::text",
    )

    # Recreate indexes with new column type
    op.create_index("idx_task_user_id", "task", ["user_id"])
    op.create_index(
        "idx_task_user_created", "task", ["user_id", sa.text("created_at DESC")]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_task_user_created", table_name="task")
    op.drop_index("idx_task_user_id", table_name="task")

    # Revert to UUID type (may fail if data contains non-UUID strings)
    op.alter_column(
        "task",
        "user_id",
        existing_type=sa.String(length=64),
        type_=sa.Uuid(),
        existing_nullable=False,
        postgresql_using="user_id::uuid",
    )

    # Recreate indexes
    op.create_index("idx_task_user_id", "task", ["user_id"])
    op.create_index(
        "idx_task_user_created", "task", ["user_id", sa.text("created_at DESC")]
    )
