import asyncio
import contextlib
import json
from typing import Any, Callable, Dict, Optional, Set

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

from utils.logger import setup_logger

logger = setup_logger(__name__)


class StreamingBroadcaster:
    """Fan-out broadcaster that pushes streaming updates to WebSocket clients."""

    def __init__(self):
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._worker: Optional[asyncio.Task] = None
        self._snapshot_builder: Optional[Callable[[], Dict[str, Any]]] = None

    async def start(self, snapshot_builder: Optional[Callable[[], Dict[str, Any]]] = None):
        """Start background dispatcher."""
        if snapshot_builder:
            self._snapshot_builder = snapshot_builder

        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._dispatcher())
            logger.info("Streaming broadcaster worker started")

    async def stop(self):
        """Stop background dispatcher and close client connections."""
        if self._worker:
            self._worker.cancel()
            with contextlib.suppress(Exception):
                await self._worker
            self._worker = None

        async with self._lock:
            clients = list(self._clients)
            self._clients.clear()

        for client in clients:
            with contextlib.suppress(Exception):
                await client.close()

    async def connect(self, websocket: WebSocket):
        """Accept connection and send initial snapshot."""
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)

        if self._snapshot_builder:
            snapshot = self._snapshot_builder()
            await self._send(websocket, {"type": "snapshot", "payload": snapshot})

        logger.debug("WebSocket connected. Total clients: %s", len(self._clients))

    async def disconnect(self, websocket: WebSocket):
        """Remove connection from pool."""
        async with self._lock:
            self._clients.discard(websocket)
        with contextlib.suppress(Exception):
            await websocket.close()
        logger.debug("WebSocket disconnected. Total clients: %s", len(self._clients))

    async def listen(self, websocket: WebSocket):
        """Consume incoming messages to keep connection alive."""
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await self.disconnect(websocket)

    async def enqueue(self, message: Dict[str, Any]):
        """Queue message for broadcast."""
        await self._queue.put(message)

    async def _dispatcher(self):
        while True:
            message = await self._queue.get()
            await self._broadcast(message)

    async def _broadcast(self, message: Dict[str, Any]):
        async with self._lock:
            clients = list(self._clients)

        if not clients:
            return

        payload = json.dumps(message, default=self._json_serializer)

        for websocket in clients:
            try:
                await websocket.send_text(payload)
            except Exception as exc:
                logger.debug("WebSocket send failed; removing client. Error: %s", exc)
                await self.disconnect(websocket)

    @staticmethod
    async def _send(websocket: WebSocket, message: Dict[str, Any]):
        await websocket.send_text(json.dumps(message, default=StreamingBroadcaster._json_serializer))

    @staticmethod
    def _json_serializer(obj: Any):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)
