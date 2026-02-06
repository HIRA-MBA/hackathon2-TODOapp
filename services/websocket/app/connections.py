"""WebSocket Connection Manager.

Per T036, T041: Manages WebSocket connections with user-scoped messaging
and reconnection with state recovery support.
"""

import asyncio
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

logger = logging.getLogger("websocket-service")


@dataclass
class Connection:
    """Represents a WebSocket connection with metadata."""

    id: str
    websocket: WebSocket
    user_id: str
    scopes: list[str] = field(default_factory=lambda: ["own_tasks"])
    reconnect_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)
    subscribed: bool = False

    # For state recovery on reconnect
    missed_events: list[dict] = field(default_factory=list)
    last_event_time: datetime | None = None


@dataclass
class DisconnectedSession:
    """Tracks a disconnected session for state recovery."""

    user_id: str
    reconnect_token: str
    scopes: list[str]
    disconnected_at: datetime
    missed_events: list[dict] = field(default_factory=list)


class ConnectionManager:
    """Manages WebSocket connections for real-time task updates.

    Features:
    - User-scoped connections (multiple connections per user supported)
    - Reconnection with state recovery (T041)
    - Ping/pong heartbeat tracking
    - Event buffering for disconnected clients
    """

    def __init__(
        self,
        reconnect_window: int = 300,  # 5 minutes to reconnect
        max_missed_events: int = 100,
    ):
        # Active connections by connection_id
        self._connections: dict[str, Connection] = {}
        # User ID -> list of connection IDs
        self._user_connections: dict[str, list[str]] = {}
        # Disconnected sessions for reconnection (reconnect_token -> session)
        self._disconnected: dict[str, DisconnectedSession] = {}

        self.reconnect_window = timedelta(seconds=reconnect_window)
        self.max_missed_events = max_missed_events

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        reconnect_token: str | None = None,
    ) -> Connection:
        """Accept a new WebSocket connection.

        If reconnect_token is provided and valid, recovers previous state.
        """
        async with self._lock:
            connection_id = str(uuid4())

            # Check for reconnection
            missed_events = []
            scopes = ["own_tasks"]

            if reconnect_token and reconnect_token in self._disconnected:
                session = self._disconnected[reconnect_token]
                if (
                    session.user_id == user_id
                    and datetime.utcnow() - session.disconnected_at < self.reconnect_window
                ):
                    # Valid reconnection - recover state
                    missed_events = session.missed_events
                    scopes = session.scopes
                    del self._disconnected[reconnect_token]
                    logger.info(
                        "connection_recovered",
                        extra={
                            "connection_id": connection_id,
                            "user_id": user_id,
                            "missed_events": len(missed_events),
                        },
                    )

            # Accept the connection
            await websocket.accept()

            # Create connection object
            connection = Connection(
                id=connection_id,
                websocket=websocket,
                user_id=user_id,
                scopes=scopes,
                missed_events=missed_events,
            )

            # Store connection
            self._connections[connection_id] = connection
            if user_id not in self._user_connections:
                self._user_connections[user_id] = []
            self._user_connections[user_id].append(connection_id)

            logger.info(
                "connection_established",
                extra={
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "total_user_connections": len(self._user_connections[user_id]),
                },
            )

            return connection

    async def disconnect(self, connection_id: str) -> None:
        """Handle connection disconnect with state preservation for reconnection."""
        async with self._lock:
            if connection_id not in self._connections:
                return

            connection = self._connections[connection_id]

            # Store for potential reconnection
            self._disconnected[connection.reconnect_token] = DisconnectedSession(
                user_id=connection.user_id,
                reconnect_token=connection.reconnect_token,
                scopes=connection.scopes,
                disconnected_at=datetime.utcnow(),
                missed_events=[],  # Will accumulate missed events
            )

            # Remove from active connections
            del self._connections[connection_id]
            if connection.user_id in self._user_connections:
                self._user_connections[connection.user_id].remove(connection_id)
                if not self._user_connections[connection.user_id]:
                    del self._user_connections[connection.user_id]

            logger.info(
                "connection_closed",
                extra={
                    "connection_id": connection_id,
                    "user_id": connection.user_id,
                },
            )

            # Cleanup old disconnected sessions
            await self._cleanup_expired_sessions()

    async def _cleanup_expired_sessions(self) -> None:
        """Remove expired disconnected sessions."""
        now = datetime.utcnow()
        expired = [
            token
            for token, session in self._disconnected.items()
            if now - session.disconnected_at > self.reconnect_window
        ]
        for token in expired:
            del self._disconnected[token]

    def get_connection(self, connection_id: str) -> Connection | None:
        """Get a connection by ID."""
        return self._connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> list[Connection]:
        """Get all active connections for a user."""
        connection_ids = self._user_connections.get(user_id, [])
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]

    async def subscribe(
        self,
        connection_id: str,
        scopes: list[str] | None = None,
    ) -> bool:
        """Subscribe a connection to receive updates."""
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        connection.subscribed = True
        if scopes:
            connection.scopes = scopes

        logger.info(
            "connection_subscribed",
            extra={
                "connection_id": connection_id,
                "scopes": connection.scopes,
            },
        )
        return True

    async def unsubscribe(self, connection_id: str) -> bool:
        """Unsubscribe a connection from updates."""
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        connection.subscribed = False
        return True

    async def send_to_connection(
        self,
        connection_id: str,
        message: dict[str, Any],
    ) -> bool:
        """Send a message to a specific connection."""
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        try:
            await connection.websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(
                "send_failed",
                extra={
                    "connection_id": connection_id,
                    "error": str(e),
                },
            )
            return False

    async def broadcast_to_user(
        self,
        user_id: str,
        message: dict[str, Any],
    ) -> int:
        """Broadcast a message to all connections for a user.

        Also buffers message for disconnected sessions for potential reconnection.
        Returns the number of connections that received the message.
        """
        sent_count = 0

        # Send to active connections
        for connection in self.get_user_connections(user_id):
            if connection.subscribed:
                if await self.send_to_connection(connection.id, message):
                    sent_count += 1
                    connection.last_event_time = datetime.utcnow()

        # Buffer for disconnected sessions (for reconnection)
        for token, session in self._disconnected.items():
            if session.user_id == user_id:
                if len(session.missed_events) < self.max_missed_events:
                    session.missed_events.append(message)

        return sent_count

    async def broadcast_all(self, message: dict[str, Any]) -> int:
        """Broadcast a message to all subscribed connections."""
        sent_count = 0
        for connection in self._connections.values():
            if connection.subscribed:
                if await self.send_to_connection(connection.id, message):
                    sent_count += 1
        return sent_count

    def update_ping(self, connection_id: str) -> None:
        """Update last ping time for a connection."""
        connection = self._connections.get(connection_id)
        if connection:
            connection.last_ping = datetime.utcnow()

    def get_stats(self) -> dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self._connections),
            "total_users": len(self._user_connections),
            "disconnected_sessions": len(self._disconnected),
        }

    async def flush_missed_events(self, connection_id: str) -> int:
        """Send buffered missed events to a reconnected client."""
        connection = self._connections.get(connection_id)
        if not connection or not connection.missed_events:
            return 0

        sent_count = 0
        for event in connection.missed_events:
            if await self.send_to_connection(connection_id, event):
                sent_count += 1

        connection.missed_events = []
        return sent_count


# Global singleton instance
connection_manager = ConnectionManager()
