from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session.

    The session is automatically closed after the request completes.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
