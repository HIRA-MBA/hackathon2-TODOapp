"""WebSocket Service - Real-time Task Synchronization.

Per T038: Full WebSocket message protocol implementation.
Per T091, T093: Health endpoints and structured JSON logging.
Provides WebSocket connections for real-time task updates.
Subscribes to task-updates topic via Dapr and broadcasts to connected clients.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse

from app.connections import connection_manager
from app.auth import authenticate_token
from app.handlers import handle_task_update_event, handle_connection_message
from app.filters import get_allowed_scopes

# Configure structured JSON logging per T093
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("websocket-service")

app = FastAPI(
    title="WebSocket Service",
    description="Real-time task synchronization via WebSocket (Phase V)",
    version="1.5.0",
)


@app.get("/health")
async def health_check():
    """Liveness probe - service is running."""
    return {"status": "healthy", "service": "websocket"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - service is ready to accept traffic."""
    stats = connection_manager.get_stats()
    return {
        "status": "ready",
        "service": "websocket",
        "connections": stats,
    }


@app.get("/dapr/subscribe")
async def subscribe():
    """Dapr subscription configuration.

    Subscribes to task-updates topic for real-time sync.
    """
    subscriptions = [
        {
            "pubsubname": "pubsub",
            "topic": "task-updates",
            "route": "/events/task-update",
            "metadata": {
                "rawPayload": "false",
            },
        }
    ]
    return JSONResponse(content=subscriptions)


@app.post("/events/task-update")
async def handle_task_update(event: dict):
    """Handle task update events from Dapr pub/sub.

    Per T039: Broadcasts updates to connected WebSocket clients.
    """
    return await handle_task_update_event(event)


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None, description="JWT authentication token"),
    reconnect_token: str | None = Query(default=None, alias="reconnectToken"),
):
    """WebSocket endpoint for real-time task updates.

    Per websocket.yaml protocol:
    1. Client connects with ?token=JWT query parameter
    2. Server validates JWT and sends connection_ack
    3. Client sends subscribe message
    4. Server sends task_update messages when events arrive

    Supports reconnection with state recovery via reconnectToken.
    """
    # Authenticate the connection
    auth_result = authenticate_token(token)

    if not auth_result.success:
        # Reject connection with close code
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "payload": {
                "code": auth_result.error_code,
                "message": auth_result.error_message,
                "retryable": auth_result.error_code == "TOKEN_EXPIRED",
            },
        })
        await websocket.close(code=4001)  # Custom close code for auth failure
        return

    user_id = auth_result.user_id

    # Accept and register connection
    try:
        connection = await connection_manager.connect(
            websocket=websocket,
            user_id=user_id,
            reconnect_token=reconnect_token,
        )
    except Exception as e:
        logger.error("connection_failed", extra={"error": str(e)})
        await websocket.close(code=1011)  # Internal error
        return

    try:
        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connection_ack",
            "payload": {
                "connectionId": connection.id,
                "userId": user_id,
                "serverTime": datetime.utcnow().isoformat() + "Z",
                "reconnectToken": connection.reconnect_token,
            },
        })

        # Check for missed events from reconnection
        if connection.missed_events:
            logger.info(
                "reconnection_with_missed_events",
                extra={
                    "connection_id": connection.id,
                    "missed_count": len(connection.missed_events),
                },
            )

        # Message handling loop
        while True:
            data = await websocket.receive_json()

            # Handle the message
            response = await handle_connection_message(connection.id, data)

            # Send response if any
            if response:
                await websocket.send_json(response)

    except WebSocketDisconnect:
        logger.info(
            "websocket_disconnected",
            extra={"connection_id": connection.id, "user_id": user_id},
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            extra={"connection_id": connection.id, "error": str(e)},
        )
    finally:
        # Clean up connection
        await connection_manager.disconnect(connection.id)


# Stats endpoint for monitoring
@app.get("/stats")
async def get_stats():
    """Get WebSocket service statistics."""
    return connection_manager.get_stats()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
