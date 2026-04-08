"""Drift detection service - compares snapshots and checks policy compliance."""
from __future__ import annotations

from typing import List

from devready.daemon.models import (
    DriftReport,
    EnvironmentSnapshot,
    PolicyViolation,
    TeamPolicy,
    ToolVersion,
    VersionChange,
)


def _severity(old: str, new: str) -> str:
    try:
        o = [int(x) for x in old.split(".")]
        n = [int(x) for x in new.split(".")]
        if len(o) >= 1 and len(n) >= 1 and o[0] != n[0]:
            return "major"
        if len(o) >= 2 and len(n) >= 2 and o[1] != n[1]:
            return "minor"
    except (ValueError, IndexError):
        pass
    return "patch"


class DriftDetectionService:
    def compare_snapshots(self, snap_a: EnvironmentSnapshot, snap_b: EnvironmentSnapshot) -> DriftReport:
        a_tools = {t["name"]: t for t in snap_a.tools}
        b_tools = {t["name"]: t for t in snap_b.tools}

        added = [ToolVersion(**b_tools[n]) for n in b_tools if n not in a_tools]
        removed = [ToolVersion(**a_tools[n]) for n in a_tools if n not in b_tools]
        changes: List[VersionChange] = []

        for name in a_tools:
            if name in b_tools and a_tools[name]["version"] != b_tools[name]["version"]:
                changes.append(VersionChange(
                    tool_name=name,
                    old_version=a_tools[name]["version"],
                    new_version=b_tools[name]["version"],
                    severity=_severity(a_tools[name]["version"], b_tools[name]["version"]),
                ))

        drift_score = self.calculate_drift_score(len(added), len(removed), len(changes))

        return DriftReport(
            snapshot_a_id=snap_a.id or "",
            snapshot_b_id=snap_b.id or "",
            added_tools=added,
            removed_tools=removed,
            version_changes=changes,
            drift_score=drift_score,
        )

    def calculate_drift_score(self, added: int, removed: int, changed: int) -> int:
        total = added + removed + changed
        return min(100, total * 10)

    def check_policy_compliance(
        self, snapshot: EnvironmentSnapshot, policy: TeamPolicy
    ) -> List[PolicyViolation]:
        violations: List[PolicyViolation] = []
        tool_map = {t["name"]: t["version"] for t in snapshot.tools}

        for req in policy.required_tools:
            if req.name not in tool_map:
                violations.append(PolicyViolation(
                    violation_type="missing_tool",
                    tool_or_var_name=req.name,
                    expected=req.min_version,
                    actual=None,
                    severity="error",
                    message=f"Required tool '{req.name}' is not installed",
                ))
            elif req.min_version and tool_map[req.name] < req.min_version:
                violations.append(PolicyViolation(
                    violation_type="version_mismatch",
                    tool_or_var_name=req.name,
                    expected=f">={req.min_version}",
                    actual=tool_map[req.name],
                    severity="error",
                    message=f"Tool '{req.name}' version {tool_map[req.name]} < required {req.min_version}",
                ))

        for forbidden in policy.forbidden_tools:
            if forbidden in tool_map:
                violations.append(PolicyViolation(
                    violation_type="forbidden_tool",
                    tool_or_var_name=forbidden,
                    severity="error",
                    message=f"Forbidden tool '{forbidden}' is installed",
                ))

        for req in policy.env_var_requirements:
            if req.required and req.name not in snapshot.env_vars:
                violations.append(PolicyViolation(
                    violation_type="missing_env_var",
                    tool_or_var_name=req.name,
                    severity="warning",
                    message=f"Required environment variable '{req.name}' is not set",
                ))

        return violations
