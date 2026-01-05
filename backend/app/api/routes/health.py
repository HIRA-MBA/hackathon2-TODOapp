from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint.

    Returns server health status and database connectivity.
    Per openapi.yaml: No auth required for health check.
    """
    try:
        # Test database connection
        await session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "error": None,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
