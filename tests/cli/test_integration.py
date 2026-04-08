import pytest
from typer.testing import CliRunner
from devready.cli.main import app
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.fixture
def runner():
    return CliRunner()

def test_scan_command(runner):
    # We need to mock the DaemonClient within the CLIContext
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        # The scan method is async, so we use AsyncMock for its return value
        mock_client.scan = AsyncMock(return_value={
            "health_score": 90,
            "tools": [{"name": "python", "version": "3.11.0", "status": "ok"}]
        })
        
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0
        assert "Health Score: 90/100" in result.stdout

def test_status_command(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_latest_snapshot = AsyncMock(return_value={
            "health_score": 85,
            "tools": [{"name": "node", "version": "18.0.0", "status": "ok"}]
        })
        
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Health Score: 85/100" in result.stdout

def test_drift_command_with_baseline(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_latest_snapshot = AsyncMock(return_value={"id": "current-id"})
        mock_client.get_snapshot = AsyncMock(return_value={"id": "base-id"})
        mock_client.compare_drift = AsyncMock(return_value={
            "added_tools": [],
            "removed_tools": [],
            "version_changes": [],
            "drift_score": 10
        })
        
        result = runner.invoke(app, ["drift", "--baseline", "base-id"])
        # print(result.stdout)
        assert result.exit_code == 0
        assert "Drift Score: 10/100" in result.stdout

def test_json_output(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.scan = AsyncMock(return_value={"health_score": 100})
        
        result = runner.invoke(app, ["--json", "scan"])
        assert result.exit_code == 0
        assert '{"health_score": 100}' in result.stdout

def test_fix_command(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_latest_snapshot = AsyncMock(return_value={
            "snapshot_id": "123",
        })
        mock_client.get_fix_recommendations = AsyncMock(return_value=[
            {"fix_id": "fix-1", "issue_description": "Test Fix", "command": "echo fix", "confidence": "high"}
        ])
        mock_client.apply_fixes = AsyncMock(return_value={"results": [{"fix_id": "fix-1", "success": True, "message": "done"}]})

        # Test dry run
        result = runner.invoke(app, ["fix", "--dry-run"])
        assert result.exit_code == 0
        assert "Test Fix" in result.stdout
        mock_client.apply_fixes.assert_not_called()

        # Test apply with auto-approve
        result = runner.invoke(app, ["fix", "-y"])
        assert result.exit_code == 0
        assert "Fixes applied successfully!" in result.stdout
        mock_client.apply_fixes.assert_called_once()

def test_team_status_command(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_team_summary = AsyncMock(return_value={
            "team_name": "Test Team",
            "aggregate_score": 88,
            "members": [
                {"name": "Alice", "score": 95, "status": "online", "last_scan": "1m ago"}
            ]
        })
        
        result = runner.invoke(app, ["team", "status"])
        assert result.exit_code == 0
        assert "Team: Test Team (Avg: 88%)" in result.stdout
        assert "Alice" in result.stdout

def test_team_sync_command(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.sync_team_data = AsyncMock(return_value={"status": "success"})
        
        # Use --quiet on the root command to bypass confirmation
        result = runner.invoke(app, ["-q", "team", "sync"])
        assert result.exit_code == 0
        assert "Successfully synced with team hub" in result.stdout
