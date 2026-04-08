"""
Demo scenario tests for the health score system with a realistic TeamPolicy.
Covers: severity-weighted deductions, version distance grading, forbidden tools,
missing env vars, and baseline (no-policy) scoring.
"""
import pytest

from devready.daemon.models import (
    EnvVarRequirement,
    EnvironmentSnapshot,
    TeamPolicy,
    ToolRequirement,
)
from devready.daemon.services.health_calculator import HealthScoreCalculator

calc = HealthScoreCalculator()

# ---------------------------------------------------------------------------
# Shared demo policy: a realistic Python web-service team policy
# ---------------------------------------------------------------------------
DEMO_POLICY = TeamPolicy(
    required_tools=[
        ToolRequirement(name="git",    min_version="2.30.0", severity="critical"),
        ToolRequirement(name="python", min_version="3.11.0", severity="critical"),
        ToolRequirement(name="docker", min_version="24.2.0", severity="warning"),  # actual will be 24.0.0 → minor gap
        ToolRequirement(name="node",   min_version="18.0.0", severity="info"),
    ],
    forbidden_tools=["pip2", "python2"],
    env_var_requirements=[
        EnvVarRequirement(name="DATABASE_URL", required=True),
        EnvVarRequirement(name="SECRET_KEY",   required=True),
        EnvVarRequirement(name="DEBUG",        required=False),
    ],
)


def _snap(tools: list[dict], env_vars: dict | None = None) -> EnvironmentSnapshot:
    return EnvironmentSnapshot(
        project_path="/demo/myservice",
        project_name="myservice",
        tools=tools,
        dependencies={},
        env_vars=env_vars or {},
        health_score=0,
        scan_duration_seconds=0.5,
    )


# ---------------------------------------------------------------------------
# Scenario 1: Perfect compliance → 100
# ---------------------------------------------------------------------------
def test_perfect_compliance_scores_100():
    snap = _snap(
        tools=[
            {"name": "git",    "version": "2.43.0", "path": "/usr/bin/git"},
            {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
            {"name": "docker", "version": "25.0.1", "path": "/usr/bin/docker"},
            {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
        ],
        env_vars={"DATABASE_URL": "postgres://...", "SECRET_KEY": "abc"},
    )
    assert calc.calculate_score(snap, DEMO_POLICY) == 100


# ---------------------------------------------------------------------------
# Scenario 2: Missing critical tool (git) → heavy deduction
# ---------------------------------------------------------------------------
def test_missing_critical_tool_heavy_deduction():
    snap = _snap(
        tools=[
            {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
            {"name": "docker", "version": "25.0.1", "path": "/usr/bin/docker"},
            {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
        ],
        env_vars={"DATABASE_URL": "postgres://...", "SECRET_KEY": "abc"},
    )
    score = calc.calculate_score(snap, DEMO_POLICY)
    assert score == 75  # -25 for missing critical git


# ---------------------------------------------------------------------------
# Scenario 3: Version too old — major gap on critical tool
# ---------------------------------------------------------------------------
def test_major_version_gap_on_critical_tool():
    snap = _snap(
        tools=[
            {"name": "git",    "version": "1.9.0",  "path": "/usr/bin/git"},   # major gap
            {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
            {"name": "docker", "version": "25.0.1", "path": "/usr/bin/docker"},
            {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
        ],
        env_vars={"DATABASE_URL": "postgres://...", "SECRET_KEY": "abc"},
    )
    score = calc.calculate_score(snap, DEMO_POLICY)
    assert score == 85  # -15 (critical × major)


# ---------------------------------------------------------------------------
# Scenario 4: Minor version gap on warning tool
# ---------------------------------------------------------------------------
def test_minor_version_gap_on_warning_tool():
    snap = _snap(
        tools=[
            {"name": "git",    "version": "2.43.0", "path": "/usr/bin/git"},
            {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
            {"name": "docker", "version": "24.0.0", "path": "/usr/bin/docker"},  # minor gap vs required 24.2.0
            {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
        ],
        env_vars={"DATABASE_URL": "postgres://...", "SECRET_KEY": "abc"},
    )
    score = calc.calculate_score(snap, DEMO_POLICY)
    assert score == 97  # -3 (warning × minor = round(5 * 0.6) = 3)


# ---------------------------------------------------------------------------
# Scenario 5: Forbidden tool present
# ---------------------------------------------------------------------------
def test_forbidden_tool_deducts_points():
    snap = _snap(
        tools=[
            {"name": "git",    "version": "2.43.0", "path": "/usr/bin/git"},
            {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
            {"name": "docker", "version": "25.0.1", "path": "/usr/bin/docker"},
            {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
            {"name": "python2","version": "2.7.18", "path": "/usr/bin/python2"},
        ],
        env_vars={"DATABASE_URL": "postgres://...", "SECRET_KEY": "abc"},
    )
    score = calc.calculate_score(snap, DEMO_POLICY)
    assert score == 85  # -15 for forbidden python2


# ---------------------------------------------------------------------------
# Scenario 6: Missing required env vars
# ---------------------------------------------------------------------------
def test_missing_env_vars_deduct_points():
    snap = _snap(
        tools=[
            {"name": "git",    "version": "2.43.0", "path": "/usr/bin/git"},
            {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
            {"name": "docker", "version": "25.0.1", "path": "/usr/bin/docker"},
            {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
        ],
        env_vars={},  # both required vars missing
    )
    score = calc.calculate_score(snap, DEMO_POLICY)
    assert score == 90  # -5 × 2 missing required vars


# ---------------------------------------------------------------------------
# Scenario 7: Worst case — everything wrong
# ---------------------------------------------------------------------------
def test_worst_case_floors_at_zero():
    snap = _snap(
        tools=[
            {"name": "python2", "version": "2.7.18", "path": "/usr/bin/python2"},
            {"name": "pip2",    "version": "9.0.0",  "path": "/usr/bin/pip2"},
        ],
        env_vars={},
    )
    score = calc.calculate_score(snap, DEMO_POLICY)
    assert score == 0


# ---------------------------------------------------------------------------
# Scenario 8: Baseline (no policy) — no tools
# ---------------------------------------------------------------------------
def test_baseline_no_tools():
    snap = _snap(tools=[])
    assert calc.calculate_score(snap, None) == 30


# ---------------------------------------------------------------------------
# Scenario 9: Baseline — well-equipped environment
# ---------------------------------------------------------------------------
def test_baseline_well_equipped():
    snap = _snap(tools=[
        {"name": "git",    "version": "2.43.0", "path": "/usr/bin/git"},
        {"name": "python", "version": "3.12.0", "path": "/usr/bin/python"},
        {"name": "docker", "version": "25.0.1", "path": "/usr/bin/docker"},
        {"name": "node",   "version": "20.0.0", "path": "/usr/bin/node"},
        {"name": "make",   "version": "4.3",    "path": "/usr/bin/make"},
    ])
    score = calc.calculate_score(snap, None)
    assert score > 70
