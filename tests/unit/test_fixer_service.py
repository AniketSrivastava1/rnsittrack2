import pytest
from unittest.mock import patch, MagicMock
from devready.daemon.services.fixer_service import FixerService, FixRecommendation
from devready.daemon.models import PolicyViolation
from devready.inspector.subprocess_wrapper import ExecutionResult

@pytest.fixture
def fixer_service():
    return FixerService()

def test_get_recommendations_missing_tool(fixer_service):
    violation = PolicyViolation(
        violation_type="missing_tool",
        tool_or_var_name="node",
        severity="error",
        message="Node.js is missing"
    )
    recs = fixer_service.get_recommendations([violation])
    assert len(recs) == 1
    assert recs[0].strategy == "install_tool"
    assert "mise install node" in recs[0].command

def test_get_recommendations_version_mismatch(fixer_service):
    violation = PolicyViolation(
        violation_type="version_mismatch",
        tool_or_var_name="node",
        expected="20.0.0",
        actual="18.0.0",
        severity="warning",
        message="Node.js version mismatch"
    )
    recs = fixer_service.get_recommendations([violation])
    assert len(recs) == 1
    assert recs[0].strategy == "update_tool"
    assert "mise use node@20.0.0" in recs[0].command

@pytest.mark.asyncio
async def test_apply_fix_success(fixer_service):
    # Use unittest.mock.patch instead of mocker fixture
    with patch("devready.inspector.subprocess_wrapper.SubprocessWrapper.execute") as mock_execute:
        mock_execute.return_value = ExecutionResult(
            command="nvm install node",
            stdout="Success",
            stderr="",
            exit_code=0,
            duration_ms=100.0
        )

        rec = FixRecommendation(
            violation=PolicyViolation(
                violation_type="missing_tool",
                tool_or_var_name="node",
                severity="error",
                message="Node.js is missing"
            ),
            strategy="install_tool",
            command="nvm install node",
            description="Install Node.js"
        )
        
        result = await fixer_service.apply_fix(rec)
        assert result.success is True
        assert "Successfully applied fix" in result.message
