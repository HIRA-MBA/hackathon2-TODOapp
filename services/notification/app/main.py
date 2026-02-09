"""Notification Service - Dapr Pub/Sub Consumer.

Per T076-T083: Subscribes to reminders topic and handles notification delivery
with quiet hours respect and multi-channel support.
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.handlers import (
    ReminderEvent,
    handle_reminder_trigger,
    process_pending_notifications,
)
from app.scheduler import run_scheduler

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("notification-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Notification service starting")
    # Start the reminder scheduler as a background task
    scheduler_task = asyncio.create_task(run_scheduler())
    logger.info("Reminder scheduler background task started")
    yield
    # Cancel the scheduler on shutdown
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    logger.info("Notification service shutting down")


app = FastAPI(
    title="Notification Service",
    description="Handles reminder delivery and notifications via Dapr pub/sub",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Liveness probe - service is running.

    Per T090: Health endpoint for Kubernetes probes.
    """
    return {"status": "healthy", "service": "notification"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - service is ready to accept traffic.

    Per T090: Readiness check for traffic routing.
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
        "service": "notification",
        "checks": checks,
    }


@app.get("/dapr/subscribe")
async def subscribe():
    """Dapr subscription configuration.

    Per T076: Tells Dapr which topics this service subscribes to.
    """
    subscriptions = [
        {
            "pubsubname": "pubsub",
            "topic": "reminders",
            "route": "/events/reminder",
            "metadata": {
                "rawPayload": "false",
            },
        },
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task",
            "metadata": {
                "rawPayload": "false",
            },
        },
    ]
    logger.info(f"Dapr subscription config requested: {subscriptions}")
    return JSONResponse(content=subscriptions)


@app.post("/events/reminder")
async def handle_reminder_event(request: Request):
    """Handle reminder events from Dapr pub/sub.

    Per T077: Processes reminder trigger events and delivers notifications.
    """
    try:
        body = await request.json()
        logger.info(f"Received reminder event: type={body.get('type', 'unknown')}, id={body.get('id', 'unknown')}")

        event_type = body.get("type", "")

        # Only process reminder.trigger events
        if event_type != "com.todo.reminder.trigger":
            logger.debug(f"Ignoring event type: {event_type}")
            return {"status": "IGNORED", "reason": f"not reminder.trigger: {event_type}"}

        # Parse and handle the event
        event = ReminderEvent.model_validate(body)
        result = await handle_reminder_trigger(event)

        logger.info(f"Event {event.id} processed: {result}")
        return result

    except Exception as e:
        logger.exception(f"Error processing reminder event: {e}")
        return {"status": "ERROR", "reason": str(e)}


@app.post("/events/task")
async def handle_task_event(request: Request):
    """Handle task events for notification-related processing.

    Listens for task updates that might affect scheduled reminders.
    """
    try:
        body = await request.json()
        event_type = body.get("type", "")
        logger.info(f"Received task event: {event_type}")

        # Handle task deletion - cancel pending reminders
        if event_type == "com.todo.task.deleted":
            task_id = body.get("data", {}).get("taskId")
            logger.info(f"Task {task_id} deleted, would cancel pending reminders")
            # TODO: Cancel scheduled reminders for deleted task

        # Handle task update - reschedule reminders if due_date changed
        elif event_type == "com.todo.task.updated":
            task_id = body.get("data", {}).get("task", {}).get("id")
            logger.info(f"Task {task_id} updated, would check reminder schedule")
            # TODO: Reschedule reminder if due_date changed

        return {"status": "SUCCESS"}

    except Exception as e:
        logger.exception(f"Error processing task event: {e}")
        return {"status": "ERROR", "reason": str(e)}


@app.post("/admin/process-pending")
async def trigger_pending_processing():
    """Admin endpoint to process pending notifications.

    Per T083: Triggers batch processing of deferred notifications.

    This would normally be called by a scheduled job after quiet hours end.
    """
    result = await process_pending_notifications()
    logger.info(f"Processed pending notifications: {result}")
    return result


@app.get("/")
async def root():
    """Root endpoint for service discovery."""
    return {
        "service": "notification-service",
        "version": "1.0.0",
        "description": "Handles reminder delivery and notifications",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
