import pytest
import asyncio
from devready.cli.dashboard import DevReadyDashboard, HealthWidget
from devready.cli.daemon_client import DaemonClient
from unittest.mock import MagicMock, AsyncMock, patch
from textual.widgets import DataTable
import os

@pytest.mark.asyncio
async def test_dashboard_mount_and_data():
    mock_client = MagicMock(spec=DaemonClient)
    mock_client.base_url = "http://localhost:8443"
    mock_client.get_latest_snapshot = AsyncMock(return_value={
        "health_score": 90,
        "tools": [{"name": "python", "version": "3.11", "path": "/bin/python", "manager": "system", "status": "ok"}]
    })
    mock_client.get_team_summary = AsyncMock(return_value={"members": []})
    
    with patch.object(DevReadyDashboard, "listen_to_daemon", return_value=None):
        app = DevReadyDashboard(mock_client)
        async with app.run_test() as pilot:
            snapshot = {
                "health_score": 90,
                "tools": [{"name": "python", "version": "3.11", "path": "/bin/python", "manager": "system", "status": "ok"}]
            }
            app.update_ui(snapshot)
            await pilot.pause()
            
            health = app.query_one("#health-score", HealthWidget)
            assert health.score == 90
            
            table = app.query_one("#tools-table", DataTable)
            assert table.row_count == 1
            
            assert "✅ Health Score" in health.render()

@pytest.mark.asyncio
async def test_dashboard_refresh_action():
    mock_client = MagicMock(spec=DaemonClient)
    mock_client.base_url = "http://localhost:8443"
    mock_client.get_latest_snapshot = AsyncMock(return_value={"health_score": 90, "tools": []})
    mock_client.get_team_summary = AsyncMock(return_value={"members": []})
    
    with patch.object(DevReadyDashboard, "listen_to_daemon", return_value=None):
        app = DevReadyDashboard(mock_client)
        async with app.run_test() as pilot:
            app.update_ui({"health_score": 90, "tools": []})
            await pilot.pause()
            
            health = app.query_one("#health-score", HealthWidget)
            assert health.score == 90
            
            app.update_ui({"health_score": 95, "tools": []})
            await pilot.pause()
            
            assert health.score == 95
