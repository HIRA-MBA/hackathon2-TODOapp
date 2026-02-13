"""Create message table for Phase 3 AI Chatbot

Revision ID: 004
Revises: 003
Create Date: 2026-01-04

Per spec FR-009: System MUST persist all messages (user and assistant)
with timestamps and conversation references.

Message roles: user, assistant, tool (per spec clarification).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'tool')",
            name="ck_message_role",
        ),
    )
    # Composite index for fetching recent messages in a conversation
    op.create_index(
        "idx_message_conversation_created",
        "message",
        ["conversation_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_message_conversation_created", table_name="message")
    op.drop_table("message")
