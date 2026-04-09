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


def _version_satisfies(actual: str, min_version: str) -> bool:
    try:
        a = tuple(int(x) for x in actual.split(".") if x.isdigit())
        m = tuple(int(x) for x in min_version.split(".") if x.isdigit())
        length = max(len(a), len(m))
        a += (0,) * (length - len(a))
        m += (0,) * (length - len(m))
        return a >= m
    except Exception:
        return actual >= min_version


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

        drift_score = self._weighted_drift_score(added, removed, changes)
        
        # Check AI Config drift
        ai_config_changed = False
        if snap_a.ai_configs != snap_b.ai_configs:
            ai_config_changed = True
            drift_score = min(100, drift_score + 10)  # Minor penalty for AI drift

        return DriftReport(
            snapshot_a_id=snap_a.id or "",
            snapshot_b_id=snap_b.id or "",
            added_tools=added,
            removed_tools=removed,
            version_changes=changes,
            drift_score=drift_score,
            ai_config_changed=ai_config_changed,
        )

    def _weighted_drift_score(self, added: list, removed: list, changes: List[VersionChange]) -> int:
        score = len(removed) * 15 + len(added) * 5
        for c in changes:
            score += {"major": 20, "minor": 8, "patch": 3}.get(c.severity, 5)
        return min(100, score)

    def calculate_drift_score(self, added: int, removed: int, changed: int) -> int:
        """Kept for backwards compatibility."""
        return min(100, removed * 15 + changed * 10 + added * 5)

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
            else:
                actual = tool_map[req.name]
                too_old = req.min_version and not _version_satisfies(actual, req.min_version)
                too_new = req.max_version and _version_satisfies(actual, req.max_version) and actual != req.max_version
                # too_new: actual > max_version
                if req.max_version:
                    a = tuple(int(x) for x in actual.split(".") if x.isdigit())
                    m = tuple(int(x) for x in req.max_version.split(".") if x.isdigit())
                    too_new = a > m
                if too_old:
                    violations.append(PolicyViolation(
                        violation_type="version_mismatch",
                        tool_or_var_name=req.name,
                        expected=f">={req.min_version}",
                        actual=actual,
                        severity="error",
                        message=f"Tool '{req.name}' version {actual} is below required {req.min_version}",
                    ))
                elif too_new:
                    violations.append(PolicyViolation(
                        violation_type="version_mismatch",
                        tool_or_var_name=req.name,
                        expected=f"<={req.max_version}",
                        actual=actual,
                        severity="error",
                        message=f"Tool '{req.name}' version {actual} exceeds maximum allowed {req.max_version}",
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

        # Check AI Configs Drift
        instructions = str(snapshot.ai_configs.get("instructions", "")).lower()
        for required_text in policy.ai_instructions_must_contain:
            if required_text.lower() not in instructions:
                violations.append(PolicyViolation(
                    violation_type="ai_config_drift",
                    tool_or_var_name=f"AI Config: {required_text}",
                    severity="warning",
                    message=f"AI agent config is missing required rule: '{required_text}'",
                ))

        return violations
