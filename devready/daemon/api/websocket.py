"""WebSocket endpoint for real-time scan progress."""
from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from devready.daemon.websocket.manager import WebSocketManager

router = APIRouter()
manager = WebSocketManager()
logger = logging.getLogger(__name__)


@router.websocket("/ws/scan")
async def scan_websocket(websocket: WebSocket, project_path: str = "/"):
    await manager.connect(websocket, project_path)
    try:
        while True:
            # Keep connection alive; scan progress is pushed via manager.broadcast()
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_path)
