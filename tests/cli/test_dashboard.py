import pytest
from devready.cli.dashboard import DevReadyDashboard
from devready.cli.daemon_client import DaemonClient
from unittest.mock import MagicMock, AsyncMock


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
        # Dashboard composes without error and has the tools table
        table = app.query_one("#tools-table")
        assert table is not None


@pytest.mark.asyncio
async def test_dashboard_refresh_action():
    mock_client = MagicMock(spec=DaemonClient)
    mock_client.base_url = "http://localhost:8443"
    mock_client.get_latest_snapshot = AsyncMock(return_value={"health_score": 50, "tools": []})

    app = DevReadyDashboard(mock_client)
    async with app.run_test() as pilot:
        # r key triggers refresh without crashing
        await pilot.press("r")
        await pilot.pause()
        assert app.query_one("#tools-table") is not None
