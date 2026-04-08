"""Unit tests for WebSocket manager."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from devready.daemon.websocket.manager import WebSocketManager


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    mgr = WebSocketManager()
    ws = AsyncMock()
    await mgr.connect(ws, "/proj")
    assert ws in mgr._connections["/proj"]

    mgr.disconnect(ws, "/proj")
    assert ws not in mgr._connections["/proj"]


@pytest.mark.asyncio
async def test_broadcast_sends_to_all_clients():
    mgr = WebSocketManager()
    ws1, ws2 = AsyncMock(), AsyncMock()
    await mgr.connect(ws1, "/proj")
    await mgr.connect(ws2, "/proj")

    msg = {"type": "progress", "stage": "scanning", "percent_complete": 50, "current_tool": "node", "message": "Scanning..."}
    await mgr.broadcast("/proj", msg)

    ws1.send_json.assert_called_once_with(msg)
    ws2.send_json.assert_called_once_with(msg)


@pytest.mark.asyncio
async def test_broadcast_handles_failed_send():
    """Failed sends should not affect other clients."""
    mgr = WebSocketManager()
    ws1, ws2 = AsyncMock(), AsyncMock()
    ws1.send_json.side_effect = Exception("connection closed")
    await mgr.connect(ws1, "/proj")
    await mgr.connect(ws2, "/proj")

    await mgr.broadcast("/proj", {"type": "progress", "stage": "test", "percent_complete": 0, "current_tool": "", "message": ""})
    ws2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_progress_message_has_required_fields():
    """
    Feature: architect-core-api-data-state, Property 27: Progress Messages Contain Required Fields
    Validates: Requirements 7.3
    """
    mgr = WebSocketManager()
    ws = AsyncMock()
    await mgr.connect(ws, "/proj")

    msg = {"type": "progress", "stage": "scanning_tools", "percent_complete": 45, "current_tool": "node", "message": "Detecting Node.js"}
    await mgr.broadcast("/proj", msg)

    sent = ws.send_json.call_args[0][0]
    assert "stage" in sent
    assert "percent_complete" in sent
    assert "current_tool" in sent
    assert "message" in sent
