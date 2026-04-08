"""
Property tests for health score calculation.
Feature: architect-core-api-data-state
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from devready.daemon.models import EnvironmentSnapshot, TeamPolicy, ToolRequirement
from devready.daemon.services.health_calculator import HealthScoreCalculator
from tests.strategies import team_policy_strategy, tool_version_strategy


def _make_snap(tools=None, env_vars=None) -> EnvironmentSnapshot:
    return EnvironmentSnapshot(
        project_path="/test",
        project_name="test",
        tools=[t.model_dump() for t in (tools or [])],
        dependencies={},
        env_vars=env_vars or {},
        health_score=0,
        scan_duration_seconds=1.0,
    )


calc = HealthScoreCalculator()


@given(tools=st.lists(tool_version_strategy(), max_size=10), policy=team_policy_strategy())
@settings(max_examples=100)
def test_health_score_always_in_range(tools, policy):
    """
    Feature: architect-core-api-data-state, Property 21: Health Score Within Valid Range
    Validates: Requirements 6.1
    """
    snap = _make_snap(tools)
    score = calc.calculate_score(snap, policy)
    assert 0 <= score <= 100


@given(policy=team_policy_strategy())
@settings(max_examples=50)
def test_perfect_compliance_yields_100(policy):
    """
    Feature: architect-core-api-data-state, Property 23: Perfect Compliance Yields Maximum Score
    Validates: Requirements 6.5
    """
    from devready.daemon.models import ToolVersion
    forbidden_set = set(policy.forbidden_tools)

    # Skip contradictory policies (tool both required and forbidden)
    required_names = {req.name for req in policy.required_tools}
    if required_names & forbidden_set:
        return  # contradiction - skip

    # Build compliant tools: all required tools present with sufficient version
    seen: dict = {}
    for req in policy.required_tools:
        seen[req.name] = req.min_version

    compliant_tools = [
        ToolVersion(name=name, version="99.0.0", path="/usr/bin/" + name)
        for name in seen
    ]
    snap = _make_snap(compliant_tools)
    score = calc.calculate_score(snap, policy)

    # No env var requirements in our strategy, so score should be 100
    if not policy.env_var_requirements:
        assert score == 100


def test_missing_required_tool_deducts_points():
    """
    Feature: architect-core-api-data-state, Property 22: Health Score Decreases with Policy Violations
    Validates: Requirements 6.2
    """
    policy = TeamPolicy(required_tools=[ToolRequirement(name="node")])
    snap_with = _make_snap()
    snap_without = _make_snap()

    score_without = calc.calculate_score(snap_without, policy)
    assert score_without <= 90  # -10 for missing tool


def test_baseline_score_without_policy():
    """
    Feature: architect-core-api-data-state, Property 24: Baseline Score Without Policy
    Validates: Requirements 6.6
    """
    snap = _make_snap()
    score = calc.calculate_score(snap, None)
    assert 0 <= score <= 100
