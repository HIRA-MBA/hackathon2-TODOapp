"""Add chatkit_session table

Revision ID: 2622ddabaf3c
Revises: 005
Create Date: 2026-01-21 19:47:56.148701

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "2622ddabaf3c"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chatkit_session table for token exchange authentication
    op.create_table(
        "chatkit_session",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column(
            "user_id", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_chatkit_session_token"), "chatkit_session", ["token"], unique=True
    )
    op.create_index(
        op.f("ix_chatkit_session_user_id"), "chatkit_session", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chatkit_session_user_id"), table_name="chatkit_session")
    op.drop_index(op.f("ix_chatkit_session_token"), table_name="chatkit_session")
    op.drop_table("chatkit_session")
