"""`.devready.yml` environment contract loader and validator."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, ValidationError

from devready.daemon.models import EnvVarRequirement, PolicyViolation, TeamPolicy, ToolRequirement


class ContractParseError(ValueError):
    pass


class ContractTool(BaseModel):
    name: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    allowed_managers: Optional[List[str]] = None


class ContractEnvVar(BaseModel):
    name: str
    required: bool = True
    pattern: Optional[str] = None


class EnvContract(BaseModel):
    version: str = "1"
    min_health_score: int = 90
    required_tools: List[ContractTool] = []
    forbidden_tools: List[str] = []
    env_vars: List[ContractEnvVar] = []


def load_contract(project_path: str) -> EnvContract:
    path = Path(project_path) / ".devready.yml"
    if not path.exists():
        raise FileNotFoundError(f"No .devready.yml found in {project_path}")
    try:
        data = yaml.safe_load(path.read_text())
        return EnvContract(**(data or {}))
    except (yaml.YAMLError, ValidationError) as e:
        raise ContractParseError(f"Malformed .devready.yml: {e}") from e


def contract_to_team_policy(contract: EnvContract) -> TeamPolicy:
    return TeamPolicy(
        required_tools=[ToolRequirement(name=t.name, min_version=t.min_version,
                                        max_version=t.max_version, allowed_managers=t.allowed_managers)
                        for t in contract.required_tools],
        forbidden_tools=contract.forbidden_tools,
        version_constraints={t.name: t.min_version for t in contract.required_tools if t.min_version},
        env_var_requirements=[EnvVarRequirement(name=e.name, required=e.required, pattern=e.pattern)
                               for e in contract.env_vars],
    )


def validate_snapshot_against_contract(snapshot, contract: EnvContract) -> List[PolicyViolation]:
    from devready.daemon.services.drift_service import DriftDetectionService
    return DriftDetectionService().check_policy_compliance(snapshot, contract_to_team_policy(contract))
