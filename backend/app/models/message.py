from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import Any
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import String


class MessageRole(str, Enum):
    """Role of a message in a conversation.

    Per spec clarification: Three roles - user, assistant, tool (for tool execution results).
    """

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(SQLModel, table=True):
    """Message entity representing a single message in a conversation.

    Per spec FR-009: System MUST persist all messages (user and assistant)
    with timestamps and conversation references.

    The 'tool' role captures tool execution results separately from assistant responses,
    per spec clarification session 2026-01-04.
    """

    __tablename__ = "message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(
        foreign_key="conversation.id", nullable=False, index=True
    )
    role: str = Field(sa_column=Column(String(20), nullable=False))
    content: str = Field(nullable=False)
    message_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
