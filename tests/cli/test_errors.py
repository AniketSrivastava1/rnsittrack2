import pytest
from typer.testing import CliRunner
from devready.cli.main import app
from devready.cli.errors import DaemonNotRunningError
from unittest.mock import patch, AsyncMock

@pytest.fixture
def runner():
    return CliRunner()

def test_daemon_not_running_error_handling(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.scan = AsyncMock(side_effect=DaemonNotRunningError())
        
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 1
        assert "✗ Error: Cannot connect to DevReady daemon" in result.stdout

def test_exit_on_low_health(runner):
    with patch("devready.cli.main.DaemonClient", autospec=True) as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.scan = AsyncMock(return_value={
            "health_score": 50,
            "tools": []
        })
        
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 1
        assert "Health Score: 50/100" in result.stdout
