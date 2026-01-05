from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field


class Task(SQLModel, table=True):
    """Task entity representing a todo item belonging to a user.

    Per data-model.md:
    - Each task belongs to exactly one user (user_id from JWT claims)
    - Tasks are ordered by created_at DESC (newest first)
    - user_id is NEVER accepted from client input

    Note: user_id is a string (not UUID) because Better Auth generates
    non-UUID string IDs like '7OMgLqJ4nHFamYC3ojPQLGv0yBoUmBrS'.
    """

    __tablename__ = "task"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(max_length=64, index=True, nullable=False)
    title: str = Field(max_length=200, nullable=False)
    description: str | None = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
