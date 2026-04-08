"""
Property tests for drift detection.
Feature: architect-core-api-data-state
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from devready.daemon.models import EnvironmentSnapshot, ToolVersion
from devready.daemon.services.drift_service import DriftDetectionService
from tests.strategies import team_policy_strategy, tool_version_strategy


def _make_snap(tools=None, project_path="/test") -> EnvironmentSnapshot:
    return EnvironmentSnapshot(
        id="snap-" + project_path[-1],
        project_path=project_path,
        project_name="test",
        tools=[t.model_dump() for t in (tools or [])],
        dependencies={},
        env_vars={},
        health_score=80,
        scan_duration_seconds=1.0,
    )


svc = DriftDetectionService()


@given(
    tools_a=st.lists(tool_version_strategy(), min_size=1, max_size=5),
    extra=st.lists(tool_version_strategy(), min_size=1, max_size=3),
)
@settings(max_examples=100)
def test_added_tools_detected(tools_a, extra):
    """
    Feature: architect-core-api-data-state, Property 17: Drift Detection Identifies Added Tools
    Validates: Requirements 5.3
    """
    # Ensure extra tools have unique names not in tools_a
    a_names = {t.name for t in tools_a}
    unique_extra = [ToolVersion(name=f"extra_{i}", version="1.0.0", path="/bin/extra") for i in range(len(extra))]
    snap_a = _make_snap(tools_a)
    snap_b = _make_snap(tools_a + unique_extra)

    report = svc.compare_snapshots(snap_a, snap_b)
    added_names = {t.name for t in report.added_tools}
    for t in unique_extra:
        assert t.name in added_names


@given(tools_b=st.lists(tool_version_strategy(), min_size=1, max_size=5))
@settings(max_examples=100)
def test_removed_tools_detected(tools_b):
    """
    Feature: architect-core-api-data-state, Property 18: Drift Detection Identifies Removed Tools
    Validates: Requirements 5.4
    """
    removed_tool = ToolVersion(name="removed_tool", version="1.0.0", path="/bin/removed")
    snap_a = _make_snap(tools_b + [removed_tool])
    snap_b = _make_snap(tools_b)

    report = svc.compare_snapshots(snap_a, snap_b)
    removed_names = {t.name for t in report.removed_tools}
    assert "removed_tool" in removed_names


def test_version_change_detected():
    """
    Feature: architect-core-api-data-state, Property 19: Drift Detection Identifies Version Changes
    Validates: Requirements 5.5
    """
    snap_a = _make_snap([ToolVersion(name="node", version="18.0.0", path="/bin/node")])
    snap_b = _make_snap([ToolVersion(name="node", version="20.0.0", path="/bin/node")])

    report = svc.compare_snapshots(snap_a, snap_b)
    assert len(report.version_changes) == 1
    assert report.version_changes[0].tool_name == "node"
    assert report.version_changes[0].old_version == "18.0.0"
    assert report.version_changes[0].new_version == "20.0.0"


def test_identical_snapshots_zero_drift():
    """
    Feature: architect-core-api-data-state, Property 20: Drift Score Correlates with Changes
    Validates: Requirements 5.6, 5.7
    """
    tools = [ToolVersion(name="node", version="20.0.0", path="/bin/node")]
    snap_a = _make_snap(tools)
    snap_b = _make_snap(tools)

    report = svc.compare_snapshots(snap_a, snap_b)
    assert report.drift_score == 0
    assert len(report.added_tools) == 0
    assert len(report.removed_tools) == 0
    assert len(report.version_changes) == 0


@given(policy=team_policy_strategy())
@settings(max_examples=50)
def test_policy_check_returns_violations(policy):
    """
    Feature: architect-core-api-data-state, Property 16: Policy Check Returns Violations
    Validates: Requirements 5.2
    """
    snap = _make_snap([])  # empty snapshot - all required tools missing
    violations = svc.check_policy_compliance(snap, policy)
    # Should have one violation per required tool
    assert len(violations) >= len(policy.required_tools)
