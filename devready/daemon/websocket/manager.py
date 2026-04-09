"""WebSocket connection manager."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: Dict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, project_path: str) -> None:
        await websocket.accept()
        self._connections[project_path].append(websocket)
        logger.info("WebSocket connected for project %s", project_path)

    def disconnect(self, websocket: WebSocket, project_path: str) -> None:
        conns = self._connections.get(project_path, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info("WebSocket disconnected for project %s", project_path)

    async def broadcast(self, project_path: str, message: dict) -> None:
        conns = list(self._connections.get(project_path, []))
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception as exc:
                logger.warning("Failed to send WebSocket message: %s", exc)
                self.disconnect(ws, project_path)
