from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class UserContext:
    """Context passed to agent tools for user-scoped operations.

    Per research Decision 6: JWT claims are validated at the endpoint level,
    and user_id is propagated via this context to all tool invocations.

    Per research Decision 7: Type-safe context propagation via generics,
    used with RunContextWrapper[UserContext] in tool definitions.

    Attributes:
        user_id: The authenticated user's ID from JWT 'sub' claim.
        email: The user's email from JWT (optional, for logging).
        db: Async database session for tool operations.
    """

    user_id: str
    email: str | None
    db: AsyncSession
