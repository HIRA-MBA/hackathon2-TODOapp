"""Service for ChatKit session token management."""

import secrets
from datetime import datetime, timedelta

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chatkit_session import ChatkitSession


# Token validity duration (24 hours by default)
TOKEN_EXPIRY_HOURS = 24


class ChatkitSessionService:
    """Service for managing ChatKit session tokens.

    Handles creation, validation, and cleanup of session tokens used
    for authenticating MCP requests from ChatKit workflows.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, user_id: str) -> str:
        """Create a new session token for a user.

        Args:
            user_id: The authenticated user's ID

        Returns:
            The generated token string
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)

        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)

        # Create session record
        session_record = ChatkitSession(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.session.add(session_record)
        await self.session.flush()

        return token

    async def validate_token(self, token: str) -> str | None:
        """Validate a session token and return the associated user_id.

        Args:
            token: The session token to validate

        Returns:
            The user_id if token is valid, None otherwise
        """
        stmt = select(ChatkitSession).where(
            ChatkitSession.token == token,
            ChatkitSession.revoked.is_(False),
            ChatkitSession.expires_at > datetime.utcnow(),
        )
        result = await self.session.execute(stmt)
        session_record = result.scalar_one_or_none()

        if session_record:
            return session_record.user_id
        return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke a session token.

        Args:
            token: The token to revoke

        Returns:
            True if token was found and revoked, False otherwise
        """
        stmt = select(ChatkitSession).where(ChatkitSession.token == token)
        result = await self.session.execute(stmt)
        session_record = result.scalar_one_or_none()

        if session_record:
            session_record.revoked = True
            await self.session.flush()
            return True
        return False

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user.

        Args:
            user_id: The user whose tokens should be revoked

        Returns:
            Number of tokens revoked
        """
        stmt = select(ChatkitSession).where(
            ChatkitSession.user_id == user_id,
            ChatkitSession.revoked.is_(False),
        )
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()

        count = 0
        for session_record in sessions:
            session_record.revoked = True
            count += 1

        if count > 0:
            await self.session.flush()
        return count

    async def cleanup_expired(self) -> int:
        """Delete expired and revoked tokens.

        Returns:
            Number of tokens deleted
        """
        stmt = delete(ChatkitSession).where(
            (ChatkitSession.expires_at < datetime.utcnow())
            | (ChatkitSession.revoked.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.rowcount
