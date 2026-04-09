"""Team policy REST endpoint — returns parsed .devready-team.yaml as JSON."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1", tags=["team-policy"])


@router.get("/team-policy")
async def get_team_policy(
    project_path: Optional[str] = Query(None, description="Absolute path to the project root"),
) -> Dict[str, Any]:
    """Load and return the .devready-team.yaml policy for the given project path.

    Returns an empty dict if no policy file is found.
    The extension calls this to avoid bundling a YAML parser.
    """
    path = project_path or os.getcwd()
    return _load_team_policy(path)


def _load_team_policy(project_path: str) -> Dict[str, Any]:
    import yaml

    candidates = [
        os.path.join(project_path, ".devready-team.yaml"),
        os.path.join(project_path, ".devready-team.yml"),
        os.path.join(project_path, ".devready-policy.yaml"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                with open(candidate, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                return data
            except Exception:
                pass
    return {}
