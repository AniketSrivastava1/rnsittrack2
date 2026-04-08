import pytest
from devready.cli.dashboard import DevReadyDashboard, HealthWidget
from devready.cli.daemon_client import DaemonClient
from unittest.mock import MagicMock, AsyncMock
import os

@pytest.mark.asyncio
async def test_dashboard_mount_and_data():
    mock_client = MagicMock(spec=DaemonClient)
    mock_client.base_url = "http://localhost:8443"
    mock_client.get_latest_snapshot = AsyncMock(return_value={
        "health_score": 92,
        "tools": [{"name": "python", "version": "3.11", "path": "/bin/python", "manager": "system", "status": "ok"}]
    })
    
    app = DevReadyDashboard(mock_client)
    async with app.run_test() as pilot:
        # Check initial widgets
        assert app.query_one("#health-score", HealthWidget).score == 92
        table = app.query_one("#tools-table")
        assert table.row_count == 1
        
        # Check health score rendering
        hw = app.query_one("#health-score", HealthWidget)
        assert "✅ Health Score" in hw.render()

@pytest.mark.asyncio
async def test_dashboard_refresh_action():
    mock_client = MagicMock(spec=DaemonClient)
    mock_client.base_url = "http://localhost:8443"
    mock_client.get_latest_snapshot = AsyncMock(return_value={"health_score": 50, "tools": []})
    
    app = DevReadyDashboard(mock_client)
    async with app.run_test() as pilot:
        # Change mock for refresh
        mock_client.get_latest_snapshot.return_value = {"health_score": 100, "tools": []}
        
        await pilot.press("r")
        await pilot.pause()
        
        assert app.query_one("#health-score", HealthWidget).score == 100
