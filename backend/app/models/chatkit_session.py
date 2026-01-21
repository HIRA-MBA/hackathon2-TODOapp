"""ChatKit session token model for token exchange authentication."""

from datetime import datetime
from uuid import uuid4
from sqlmodel import SQLModel, Field


class ChatkitSession(SQLModel, table=True):
    """ChatKit session token for authenticating MCP requests.

    When a user creates a ChatKit session, we generate a short-lived token
    that maps to their user_id. The MCP server can validate this token
    to authenticate requests from the ChatKit workflow.
    """

    __tablename__ = "chatkit_session"

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    token: str = Field(max_length=64, unique=True, index=True, nullable=False)
    user_id: str = Field(max_length=64, index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False)
