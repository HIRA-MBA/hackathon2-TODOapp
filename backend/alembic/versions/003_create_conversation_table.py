"""Create conversation table for Phase 3 AI Chatbot

Revision ID: 003
Revises: 002
Create Date: 2026-01-04

Per spec FR-008: System MUST persist all conversations with unique identifiers per user.
Single conversation per user (MVP), never auto-expires.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Index for finding user's conversation
    op.create_index("idx_conversation_user_id", "conversation", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_conversation_user_id", table_name="conversation")
    op.drop_table("conversation")
