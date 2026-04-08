"""Health score calculator for environment snapshots."""
from __future__ import annotations

from typing import List, Optional

from devready.daemon.models import EnvironmentSnapshot, TeamPolicy, ToolVersion


def _version_satisfies(actual: str, min_version: str) -> bool:
    """Check if actual version >= min_version using numeric comparison."""
    try:
        a = [int(x) for x in actual.split(".")]
        m = [int(x) for x in min_version.split(".")]
        # Pad to same length
        length = max(len(a), len(m))
        a += [0] * (length - len(a))
        m += [0] * (length - len(m))
        return a >= m
    except (ValueError, TypeError):
        return actual >= min_version  # fallback to string comparison


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
            if req.name not in tool_map:
                score -= 10
            elif req.min_version and not _version_satisfies(tool_map[req.name], req.min_version):
                score -= 5

        for forbidden in policy.forbidden_tools:
            if forbidden in tool_map:
                score -= 10

        for req in policy.env_var_requirements:
            if req.required and req.name not in snapshot.env_vars:
                score -= 2

        return max(0, score)

    def _baseline_score(self, snapshot: EnvironmentSnapshot) -> int:
        """Baseline score when no policy is provided - based on tool count."""
        if not snapshot.tools:
            return 50
        return min(100, 50 + len(snapshot.tools) * 5)
