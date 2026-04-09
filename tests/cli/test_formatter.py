import pytest
from devready.cli.formatter import RichFormatter
from io import StringIO
from rich.console import Console

@pytest.fixture
def formatter():
    return RichFormatter(no_color=True)

def test_print_health_score(formatter, capsys):
    formatter.print_health_score(95)
    captured = capsys.readouterr()
    assert "Health Score: 95/100" in captured.out

def test_print_tool_table(formatter, capsys):
    tools = [
        {"name": "python", "version": "3.11.0", "path": "/usr/bin/python", "manager": "system"},
        {"name": "node", "version": "18.0.0", "path": "/usr/local/bin/node", "manager": "nvm", "status": "outdated"}
    ]
    formatter.print_tool_table(tools)
    captured = capsys.readouterr()
    assert "python" in captured.out
    assert "3.11.0" in captured.out
    assert "OUTDATED" in captured.out

def test_print_drift_report(formatter, capsys):
    drift = {
        "added_tools": [{"name": "uv", "version": "0.1.0"}],
        "removed_tools": [{"name": "pipenv", "version": "2023.1.1"}],
        "version_changes": [{"tool_name": "ruff", "old_version": "0.1.0", "new_version": "0.2.0"}],
        "drift_score": 15
    }
    formatter.print_drift_report(drift)
    captured = capsys.readouterr()
    assert "+ uv (0.1.0)" in captured.out
    assert "- pipenv (2023.1.1)" in captured.out
    assert "ruff: 0.1.0 → 0.2.0" in captured.out
    assert "Drift Score: 15/100" in captured.out

def test_print_fix_recommendations(formatter, capsys):
    fixes = [
        {
            "title": "Upgrade Node.js",
            "description": "Node.js is outdated.",
            "auto_fix": "nvm install 20",
            "confidence": "high"
        }
    ]
    formatter.print_fix_recommendations(fixes)
    captured = capsys.readouterr()
    assert "Upgrade Node.js" in captured.out
    assert "nvm install 20" in captured.out

def test_print_error(formatter, capsys):
    formatter.print_error("Test Error", "With details")
    captured = capsys.readouterr()
    assert "✗ Error: Test Error" in captured.out
    assert "With details" in captured.out
