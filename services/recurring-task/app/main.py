"""Recurring Task Service - Dapr Pub/Sub Consumer.

Per T065-T068: Subscribes to task-events topic and creates next task instances
when recurring tasks are completed.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.handlers import TaskCompletedEvent, handle_task_completed

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("recurring-task-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Recurring task service starting")
    yield
    logger.info("Recurring task service shutting down")


app = FastAPI(
    title="Recurring Task Service",
    description="Handles automatic creation of recurring task instances via Dapr pub/sub",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Liveness probe - service is running.

    Per T089: Health endpoint for Kubernetes probes.
    """
    return {"status": "healthy", "service": "recurring-task"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - service is ready to accept traffic.

    Per T089: Readiness check for traffic routing.
    """
    # Check Dapr sidecar connectivity
    dapr_port = os.environ.get("DAPR_HTTP_PORT", "3500")
    checks = {"dapr": "unknown"}

    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://localhost:{dapr_port}/v1.0/healthz")
            checks["dapr"] = "healthy" if response.status_code == 204 else "unhealthy"
    except Exception:
        checks["dapr"] = "not available"

    return {
        "status": "ready",
        "service": "recurring-task",
        "checks": checks,
    }


@app.get("/dapr/subscribe")
async def subscribe():
    """Dapr subscription configuration.

    Per T065: Tells Dapr which topics this service subscribes to.
    See: https://docs.dapr.io/developing-applications/building-blocks/pubsub/howto-publish-subscribe/
    """
    subscriptions = [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task",
            "metadata": {
                "rawPayload": "false",
            },
        }
    ]
    logger.info(f"Dapr subscription config requested: {subscriptions}")
    return JSONResponse(content=subscriptions)


@app.post("/events/task")
async def handle_task_event(request: Request):
    """Handle task events from Dapr pub/sub.

    Per T066: Processes task.completed events to create next recurring instances.
    """
    try:
        # Parse CloudEvents envelope
        body = await request.json()
        logger.info(f"Received task event: type={body.get('type', 'unknown')}, id={body.get('id', 'unknown')}")

        event_type = body.get("type", "")

        # Only process task.completed events
        if event_type != "com.todo.task.completed":
            logger.debug(f"Ignoring event type: {event_type}")
            return {"status": "IGNORED", "reason": f"not task.completed: {event_type}"}

        # Parse and handle the event
        event = TaskCompletedEvent.model_validate(body)
        result = await handle_task_completed(event)

        logger.info(f"Event {event.id} processed: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error processing task event: {e}")
        # Return SUCCESS to prevent Dapr retry loop for parsing errors
        # Actual transient errors in handler will return ERROR
        return {"status": "ERROR", "reason": str(e)}


@app.get("/")
async def root():
    """Root endpoint for service discovery."""
    return {
        "service": "recurring-task-service",
        "version": "1.0.0",
        "description": "Handles automatic creation of recurring task instances",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
