import asyncio
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._active.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        if not self._active:
            return
        # serialize once regardless of client count, and fan out
        # concurrently instead of awaiting each socket write in sequence —
        # with hundreds/thousands of clients, doing both per-client turns
        # every event into an O(N) chain of json.dumps + blocking sends
        payload = json.dumps(message)
        clients = list(self._active)
        results = await asyncio.gather(
            *(ws.send_text(payload) for ws in clients), return_exceptions=True
        )
        for ws, result in zip(clients, results):
            if isinstance(result, Exception):
                self.disconnect(ws)
