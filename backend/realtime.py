"""WebSocket real-time fan-out.

Domain events are published from synchronous service code (which FastAPI runs
in a worker thread), so delivery is scheduled back onto the server's event
loop with ``run_coroutine_threadsafe``.
"""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

try:
    from .events import DomainEvent
except ImportError:
    from events import DomainEvent

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks live WebSocket clients with an asyncio-safe set."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, object]) -> None:
        for connection in tuple(self._connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


class RealtimeHub:
    """Adapter between the domain event broker and WebSocket clients."""

    def __init__(self, manager: ConnectionManager | None = None) -> None:
        self.manager = manager or ConnectionManager()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish(self, event: DomainEvent) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        payload: dict[str, Any] = {
            "event": event.topic,
            "payload": event.payload,
            "at": event.occurred_at.isoformat(),
        }
        asyncio.run_coroutine_threadsafe(self.manager.broadcast(payload), self._loop)

    async def handle(self, websocket: WebSocket) -> None:
        await self.manager.connect(websocket)
        try:
            await websocket.send_json({"event": "connected", "payload": {}})
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            self.manager.disconnect(websocket)
