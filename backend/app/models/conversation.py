from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field


class Conversation(SQLModel, table=True):
    """Conversation entity representing a chat session for a user.

    Per spec FR-008: System MUST persist all conversations with unique identifiers per user.
    Per research Decision 3: Single conversation per user (MVP), never auto-expires.

    Note: user_id is a string (not UUID) because Better Auth generates
    non-UUID string IDs like '7OMgLqJ4nHFamYC3ojPQLGv0yBoUmBrS'.
    """

    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(max_length=64, index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
