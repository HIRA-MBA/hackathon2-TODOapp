"""Health check endpoints for Kubernetes probes.

Per plan.md T025: Add health check endpoints (/health, /health/ready)
- /health: Liveness probe - is the service running?
- /health/ready: Readiness probe - is the service ready to accept traffic?
"""

import os

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check():
    """Liveness probe - service is running.

    Returns 200 if the service process is alive.
    Used by Kubernetes liveness probe to detect crashed containers.
    Does NOT check external dependencies (that's what readiness is for).
    """
    return {
        "status": "healthy",
        "service": "backend",
    }


@router.get("/health/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """Readiness probe - service is ready to accept traffic.

    Returns 200 only if all dependencies are available:
    - Database connection is working
    - (Future) Dapr sidecar is reachable

    Used by Kubernetes readiness probe to control traffic routing.
    """
    checks = {
        "database": "unknown",
        "dapr": "unknown",
    }
    is_ready = True

    # Check database connection
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"disconnected: {str(e)}"
        is_ready = False

    # Check Dapr sidecar (if configured)
    dapr_port = os.environ.get("DAPR_HTTP_PORT", "3500")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://localhost:{dapr_port}/v1.0/healthz")
            if response.status_code == 204:
                checks["dapr"] = "healthy"
            else:
                checks["dapr"] = f"unhealthy: status {response.status_code}"
                # Don't fail readiness if Dapr is not available (graceful degradation)
    except Exception:
        checks["dapr"] = "not available"
        # Dapr is optional for local dev without sidecars

    return {
        "status": "ready" if is_ready else "not_ready",
        "service": "backend",
        "checks": checks,
    }
