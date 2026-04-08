"""
Property tests for data models.
Feature: architect-core-api-data-state
"""
import json

import pytest
from hypothesis import given, settings
from pydantic import ValidationError

from devready.daemon.models import (
    DriftReport,
    TeamPolicy,
    ToolVersion,
)
from tests.strategies import drift_report_strategy, team_policy_strategy, tool_version_strategy


# ---------------------------------------------------------------------------
# Property 6: Model Serialization Round-Trip (Validates: Req 2.7)
# ---------------------------------------------------------------------------

@given(tool=tool_version_strategy())
@settings(max_examples=100)
def test_tool_version_round_trip(tool: ToolVersion) -> None:
    """
    Feature: architect-core-api-data-state, Property 6: Model Serialization Round-Trip
    Validates: Requirements 2.7
    """
    data = json.loads(tool.model_dump_json())
    restored = ToolVersion(**data)
    assert restored == tool


@given(report=drift_report_strategy())
@settings(max_examples=100)
def test_drift_report_round_trip(report: DriftReport) -> None:
    """
    Feature: architect-core-api-data-state, Property 6: Model Serialization Round-Trip
    Validates: Requirements 2.7
    """
    data = json.loads(report.model_dump_json())
    restored = DriftReport(**data)
    assert restored.snapshot_a_id == report.snapshot_a_id
    assert restored.drift_score == report.drift_score
    assert restored.added_tools == report.added_tools


@given(policy=team_policy_strategy())
@settings(max_examples=100)
def test_team_policy_round_trip(policy: TeamPolicy) -> None:
    """
    Feature: architect-core-api-data-state, Property 6: Model Serialization Round-Trip
    Validates: Requirements 2.7
    """
    data = json.loads(policy.model_dump_json())
    restored = TeamPolicy(**data)
    assert restored == policy


# ---------------------------------------------------------------------------
# Property 5: Invalid Model Data Raises Validation Errors (Validates: Req 2.5)
# ---------------------------------------------------------------------------

def test_tool_version_missing_required_fields() -> None:
    """
    Feature: architect-core-api-data-state, Property 5: Invalid Model Data Raises Validation Errors
    Validates: Requirements 2.5
    """
    with pytest.raises(ValidationError) as exc_info:
        ToolVersion(name="node")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    field_names = {e["loc"][0] for e in errors}
    assert "version" in field_names
    assert "path" in field_names


def test_drift_report_invalid_score() -> None:
    """
    Feature: architect-core-api-data-state, Property 5: Invalid Model Data Raises Validation Errors
    Validates: Requirements 2.5
    """
    with pytest.raises(ValidationError):
        DriftReport(
            snapshot_a_id="a",
            snapshot_b_id="b",
            drift_score=150,  # out of range
        )


def test_tool_version_is_frozen() -> None:
    """ToolVersion must be immutable (frozen=True)."""
    tool = ToolVersion(name="node", version="20.0.0", path="/usr/bin/node")
    with pytest.raises(Exception):
        tool.name = "python"  # type: ignore[misc]
