"""Health score calculator for environment snapshots."""
from __future__ import annotations

from typing import Optional

from devready.daemon.models import EnvironmentSnapshot, TeamPolicy

# Deduction weights per severity
_MISSING_TOOL_DEDUCTION = {"critical": 25, "warning": 10, "info": 3}
_VERSION_MISMATCH_DEDUCTION = {"critical": 15, "warning": 5, "info": 2}
_FORBIDDEN_TOOL_DEDUCTION = 15
_MISSING_ENV_VAR_DEDUCTION = 5

# Project-type detection: marker file -> relevant core tools
_PROJECT_PROFILES = {
    "package.json": {"node", "git"},
    "go.mod": {"go", "git"},
    "Cargo.toml": {"rust", "git"},
    "requirements.txt": {"python", "git"},
    "pyproject.toml": {"python", "git"},
    "pom.xml": {"java", "git"},
    "build.gradle": {"java", "git"},
    "Dockerfile": {"docker", "git"},
}

# Fallback universal core tools
_UNIVERSAL_CORE = {"git"}


def _version_tuple(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, TypeError):
        return (0,)


def _version_satisfies(actual: str, min_version: str) -> bool:
    a = _version_tuple(actual)
    m = _version_tuple(min_version)
    length = max(len(a), len(m))
    a += (0,) * (length - len(a))
    m += (0,) * (length - len(m))
    return a >= m


def _version_distance(actual: str, required: str) -> str:
    """Return 'major', 'minor', or 'patch' gap between actual and required."""
    a = _version_tuple(actual)
    r = _version_tuple(required)
    if len(r) > 0 and (len(a) == 0 or a[0] < r[0]):
        return "major"
    if len(r) > 1 and (len(a) < 2 or a[1] < r[1]):
        return "minor"
    return "patch"


def _detect_core_tools(project_path: str) -> set[str]:
    """Infer relevant core tools from project marker files."""
    import os
    core: set[str] = set(_UNIVERSAL_CORE)
    for marker, tools in _PROJECT_PROFILES.items():
        if os.path.exists(os.path.join(project_path, marker)):
            core |= tools
    return core if len(core) > 1 else set()  # no markers found → empty (use fallback)


class HealthScoreCalculator:
    """Computes a 0-100 health score for an environment snapshot."""

    def calculate_score(
        self,
        snapshot: EnvironmentSnapshot,
        policy: Optional[TeamPolicy] = None,
    ) -> int:
        if policy is None:
            return self._baseline_score(snapshot)

        score = 100
        tool_map = {t["name"]: t["version"] for t in snapshot.tools}

        for req in policy.required_tools:
            sev = getattr(req, "severity", "warning")
            if req.name not in tool_map:
                score -= _MISSING_TOOL_DEDUCTION.get(sev, 10)
            elif req.min_version and not _version_satisfies(tool_map[req.name], req.min_version):
                gap = _version_distance(tool_map[req.name], req.min_version)
                base = _VERSION_MISMATCH_DEDUCTION.get(sev, 5)
                # Major gap costs full deduction, minor = 60%, patch = 30%
                multiplier = {"major": 1.0, "minor": 0.6, "patch": 0.3}.get(gap, 1.0)
                score -= round(base * multiplier)

        for forbidden in policy.forbidden_tools:
            if forbidden in tool_map:
                score -= _FORBIDDEN_TOOL_DEDUCTION

        for req in policy.env_var_requirements:
            if req.required and req.name not in snapshot.env_vars:
                score -= _MISSING_ENV_VAR_DEDUCTION

        return max(0, score)

    def _baseline_score(self, snapshot: EnvironmentSnapshot) -> int:
        """Score based on project-type-aware core tool presence when no policy provided."""
        if not snapshot.tools:
            return 30

        tool_names = {t["name"].lower() for t in snapshot.tools}
        core_tools = _detect_core_tools(snapshot.project_path) or {"git", "python", "node", "docker"}

        found_core = core_tools & tool_names
        missing_core = core_tools - tool_names

        # 60 base, +5 per core tool found, -8 per core tool missing, +1 per extra tool (cap 10)
        extra = max(0, len(tool_names) - len(found_core))
        score = 60 + (len(found_core) * 5) - (len(missing_core) * 8) + min(10, extra)
        return max(0, min(100, score))
